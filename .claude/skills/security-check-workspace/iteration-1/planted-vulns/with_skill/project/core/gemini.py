"""Gemini API との通信をまとめたモジュール。"""

from __future__ import annotations

from typing import Iterator

import streamlit as st
from google import genai
from google.genai import errors, types

# API からモデル一覧を取得できなかった場合の候補
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]

# 混雑・上限超え・提供終了など、別モデルで再試行すれば成功しうるエラー
RETRYABLE_CODES = {404, 429, 500, 503}

# テキスト生成に向かないモデルを除外するためのキーワード
_EXCLUDE_KEYWORDS = (
    "tts", "image", "embedding", "live", "audio", "robotics",
    "computer-use", "native", "aqa", "learnlm", "gemma", "banana",
)


@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


@st.cache_data(ttl=3600, show_spinner=False)
def list_text_models(api_key: str) -> list[str]:
    """API キーで利用できるテキスト生成モデルの一覧を返す。"""
    try:
        names = set()
        for m in get_client(api_key).models.list():
            name = (m.name or "").removeprefix("models/")
            actions = m.supported_actions or []
            if (
                "generateContent" in actions
                and name.startswith("gemini")
                and not any(k in name for k in _EXCLUDE_KEYWORDS)
            ):
                names.add(name)
        return sorted(names, reverse=True) or FALLBACK_MODELS
    except Exception:
        return FALLBACK_MODELS


def pick_default_model(models: list[str]) -> str:
    """一覧から、安定版の Flash モデルを優先して既定値を選ぶ。"""
    def is_stable(name: str) -> bool:
        return not any(k in name for k in ("preview", "exp", "latest", "lite"))

    for cond in (
        lambda n: "flash" in n and is_stable(n),
        lambda n: "flash" in n,
        lambda n: True,
    ):
        for name in models:
            if cond(name):
                return name
    return FALLBACK_MODELS[0]


def stream_text(
    api_key: str,
    model: str,
    contents,
    system_instruction: str | None = None,
    temperature: float = 0.7,
) -> Iterator[str]:
    """Gemini の応答をストリーミングでテキストとして返す。"""
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
    )
    stream = get_client(api_key).models.generate_content_stream(
        model=model, contents=contents, config=config
    )
    for chunk in stream:
        if chunk.text:
            yield chunk.text


def file_part(data: bytes, mime_type: str) -> types.Part:
    """アップロードされたファイル（PDF など）を Gemini に渡せる形にする。"""
    return types.Part.from_bytes(data=data, mime_type=mime_type)


def to_chat_contents(messages: list[dict]) -> list[types.Content]:
    """[{role: user/assistant, content: str}] を Gemini の会話形式に変換する。"""
    return [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in messages
    ]


def stream_with_fallback(
    api_key: str,
    models: list[str],
    contents,
    system_instruction: str | None,
    temperature: float,
    info: dict,
) -> Iterator[str]:
    """models を順に試し、最初に応答したモデルの出力をストリーミングで返す。

    出力が始まる前に再試行可能なエラーが出た場合だけ次のモデルへ切り替える。
    info["model"] に実際に使ったモデル、info["skipped"] に飛ばしたモデルとエラーコードが入る。
    """
    info["skipped"] = []
    last_error: Exception | None = None
    for model in models:
        it = stream_text(api_key, model, contents, system_instruction, temperature)
        try:
            first = next(it)
        except StopIteration:
            info["model"] = model
            return
        except errors.APIError as e:
            if e.code in RETRYABLE_CODES:
                info["skipped"].append((model, e.code))
                last_error = e
                continue
            raise
        info["model"] = model
        yield first
        yield from it
        return
    if last_error:
        raise last_error
