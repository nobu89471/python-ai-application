"""フリーチャット：文章に関する相談を対話形式で行う。"""

import streamlit as st

from core.gemini import to_chat_contents
from core.ui import generate, page_header

CHAT_SYSTEM = (
    "あなたは日本語の文章作成をサポートする、親切で有能なライティングアシスタントです。"
    "文章の作成・推敲・アイデア出し・構成の相談などに、具体的かつ実用的に答えてください。"
    "必要に応じてMarkdownで見やすく整形してください。"
)


def render() -> None:
    page_header("💬 フリーチャット", "文章に関することなら何でも、対話しながら相談できます。")

    messages: list[dict] = st.session_state.setdefault("chat_messages", [])

    if messages and st.button("🧹 会話をリセット"):
        messages.clear()
        st.rerun()

    if not messages:
        st.info("例：「退職の挨拶文を考えて」「この文章をもっと魅力的にしたい」「ブログのネタを10個出して」")

    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("メッセージを入力"):
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            reply = generate(to_chat_contents(messages), system=CHAT_SYSTEM)
            if reply:
                st.markdown(reply)
                messages.append({"role": "assistant", "content": reply})
            else:
                messages.pop()  # 失敗したら送信内容を取り消す
