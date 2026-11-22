"""生成履歴（ブラウザのセッション中のみ保持）。"""

from datetime import datetime

import streamlit as st

from core.ui import page_header


def render() -> None:
    page_header("🕘 生成履歴", "このセッションで生成した結果の一覧です（ページを再読み込みすると消えます）。")

    history: list[dict] = st.session_state.get("history", [])
    if not history:
        st.info("まだ履歴はありません。")
        return

    tools = sorted({h["tool"] for h in history})
    selected = st.multiselect("ツールで絞り込み", tools, placeholder="すべて表示")
    items = [h for h in history if not selected or h["tool"] in selected]

    export = "\n\n---\n\n".join(
        f"# {h['tool']}（{h['time']}）\n\n**入力:** {h['input']}\n\n{h['output']}" for h in items
    )
    col1, col2 = st.columns(2)
    col1.download_button("💾 表示中の履歴をまとめてダウンロード", export,
                         file_name=f"history_{datetime.now():%Y%m%d_%H%M%S}.md", mime="text/markdown",
                         width="stretch")
    if col2.button("🗑️ 履歴をすべて削除", width="stretch"):
        st.session_state.history = []
        st.rerun()

    for h in items:
        with st.expander(f"{h['time']}｜{h['tool']}｜{h['input'][:40]}"):
            st.markdown(h["output"])
            st.code(h["output"], language="markdown", wrap_lines=True)
