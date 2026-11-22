"""各ツールで共通して使う UI 部品と生成処理。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import streamlit as st
from google.genai import errors

from core.gemini import stream_with_fallback

BASE_SYSTEM = (
    "あなたは日本語の文章作成を得意とする、経験豊富なプロのライター兼編集者です。"
    "ユーザーの指示に忠実に、自然で読みやすい文章を作成してください。"
    "前置きや「承知しました」などの返事は書かず、成果物だけを出力してください。"
)


ERROR_HINTS = {
    400: "リクエストが不正です。API キーが正しいか、入力内容を確認してください。",
    403: "このAPIキーでは利用できません。キーの権限や制限を確認してください。",
    404: "このモデルは現在利用できません。サイドバーで別のモデルを選んでください。",
    429: "利用上限（無料枠のレート制限など）に達しました。少し時間をおくか、別のモデルを選んでください。",
    500: "Gemini 側で一時的なエラーが発生しました。少し待って再度お試しください。",
    503: "モデルが混雑しています。少し待つか、別のモデルを選んでください。",
}

# 自動切り替え時に試す予備モデルの最大数
MAX_FALLBACKS = 3


@dataclass
class Settings:
    api_key: str
    model: str
    temperature: float
    available_models: list[str] = field(default_factory=list)

    def candidate_models(self) -> list[str]:
        """選択中のモデルを先頭に、混雑時などに切り替える予備の Flash モデルを並べる。"""
        backups = [
            m for m in self.available_models
            if m != self.model and "flash" in m and "preview" not in m
        ]
        return [self.model, *backups[:MAX_FALLBACKS]]


def get_settings() -> Settings:
    return st.session_state["settings"]


def page_header(title: str, description: str) -> None:
    st.title(title)
    st.caption(description)


def generate(
    contents,
    system: str = BASE_SYSTEM,
    temperature: float | None = None,
) -> str | None:
    """ストリーミング表示しながら生成し、完成したテキストを返す（失敗時は None）。

    選択したモデルが混雑・上限超えなどで使えない場合は、自動で予備モデルに切り替える。
    """
    s = get_settings()
    if not s.api_key:
        st.error("サイドバーで Gemini API キーを設定してください。")
        return None

    info: dict = {}
    placeholder = st.empty()
    try:
        with placeholder.container(border=True):
            st.caption(f"✍️ {s.model} で生成中…")
            text = st.write_stream(
                stream_with_fallback(
                    s.api_key,
                    s.candidate_models(),
                    contents,
                    system_instruction=system,
                    temperature=s.temperature if temperature is None else temperature,
                    info=info,
                )
            )
    except errors.APIError as e:
        placeholder.empty()
        hint = ERROR_HINTS.get(e.code, "")
        tried = "、".join(m for m, _ in info.get("skipped", []))
        st.error(
            f"Gemini API エラー（{e.code}）：{hint}"
            + (f"\n\n試したモデル：{tried}" if tried else "")
            + f"\n\n詳細：{e.message}"
        )
        return None
    except Exception as e:  # ネットワークエラーなど
        placeholder.empty()
        st.error(f"生成中にエラーが発生しました: {e}")
        return None

    placeholder.empty()
    if info.get("skipped"):
        skipped = "、".join(f"{m}（{code}）" for m, code in info["skipped"])
        st.toast(f"{skipped} が使えなかったため、{info.get('model')} で生成しました。", icon="🔁")

    text = text if isinstance(text, str) else "".join(map(str, text))
    if not text.strip():
        st.warning("応答が空でした。入力内容を変えて再度お試しください。")
        return None
    return text


def add_history(tool: str, summary: str, output: str) -> None:
    st.session_state.setdefault("history", []).insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tool": tool,
            "input": summary,
            "output": output,
        },
    )


def run_tool(result_key: str, tool_name: str, summary: str, contents, **kwargs) -> None:
    """生成→結果の保存→履歴への追加 をまとめて行う。"""
    text = generate(contents, **kwargs)
    if text:
        st.session_state[result_key] = text
        add_history(tool_name, summary, text)


def show_result(result_key: str, filename: str) -> None:
    """保存済みの生成結果を、プレビュー・コピー・ダウンロード付きで表示する。"""
    text = st.session_state.get(result_key)
    if not text:
        return

    st.divider()
    st.subheader("生成結果")
    tab_preview, tab_raw = st.tabs(["プレビュー", "テキスト（コピー用）"])
    with tab_preview:
        with st.container(border=True):
            st.markdown(text, unsafe_allow_html=True)  # 装飾タグも表示できるように
    with tab_raw:
        st.code(text, language="markdown", wrap_lines=True)

    col1, col2, col3 = st.columns([1, 1, 2])
    col1.download_button(
        "💾 ダウンロード",
        text,
        file_name=f"{filename}_{datetime.now():%Y%m%d_%H%M%S}.md",
        mime="text/markdown",
        key=f"{result_key}_dl",
        width="stretch",
    )
    if col2.button("🗑️ クリア", key=f"{result_key}_clear", width="stretch"):
        del st.session_state[result_key]
        st.rerun()
    col3.caption(f"{len(text):,} 文字")


def extra_instructions_input(key: str) -> str:
    return st.text_area(
        "追加の指示（任意）",
        key=key,
        placeholder="例：専門用語は避ける／具体例を多めに／です・ます調で",
        height=80,
    )


def optional_line(label: str, value: str) -> str:
    """値が入力されている場合だけプロンプトに含める行を作る。"""
    return f"- {label}：{value.strip()}\n" if value and value.strip() else ""
