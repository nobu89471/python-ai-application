"""要約ツール：テキストやファイル（txt / md / PDF）を要約する。"""

import streamlit as st

from core.gemini import file_part
from core.ui import extra_instructions_input, optional_line, page_header, run_tool, show_result

FORMATS = {
    "3行要約": "全体を3行（3文）で要約する",
    "箇条書き": "重要なポイントを箇条書きで5〜8個にまとめる",
    "段落の文章": "自然な文章（段落）で要約する",
    "構造化レポート": "「概要」「重要ポイント」「結論・示唆」「アクションアイテム（あれば）」の見出しで整理する",
    "一言で（TL;DR）": "一文で本質を述べる",
}
LENGTHS = ["短め", "標準", "詳しめ"]


def render() -> None:
    page_header("📄 要約", "長い文章・資料・PDF を、目的に合った形式で要約します。")

    source = st.radio("入力方法", ["テキストを貼り付け", "ファイルをアップロード"], horizontal=True, key="sum_source")
    text, uploaded = "", None
    if source == "テキストを貼り付け":
        text = st.text_area("要約したい文章 *", key="sum_text", height=280)
        if text:
            st.caption(f"{len(text):,} 文字")
    else:
        uploaded = st.file_uploader("ファイル（.txt / .md / .pdf）", type=["txt", "md", "pdf"], key="sum_file")

    col1, col2 = st.columns(2)
    fmt = col1.selectbox("要約の形式", list(FORMATS), key="sum_format")
    length = col2.select_slider("詳しさ", LENGTHS, value="標準", key="sum_length")
    purpose = st.text_input("要約の目的・注目したい観点（任意）", key="sum_purpose",
                            placeholder="例：上司への報告用／技術的な課題に注目")
    extra = extra_instructions_input("sum_extra")

    if st.button("📄 要約する", type="primary", disabled=not (text.strip() or uploaded)):
        instructions = (
            "次の内容を要約してください。\n\n"
            "## 要約の条件\n"
            f"- 形式：{FORMATS[fmt]}\n"
            f"- 詳しさ：{length}\n"
            + optional_line("目的・観点", purpose)
            + optional_line("追加の指示", extra)
            + "- 原文にない情報を付け加えない。数字や固有名詞は正確に残す\n"
            "- Markdown形式で出力する\n"
        )
        if uploaded:
            data = uploaded.getvalue()
            if uploaded.name.lower().endswith(".pdf"):
                contents = [file_part(data, "application/pdf"), instructions]
            else:
                contents = f"{instructions}\n## 原文\n{data.decode('utf-8', errors='replace')}"
            summary = f"ファイル: {uploaded.name}"
        else:
            contents = f"{instructions}\n## 原文\n{text}"
            summary = text.strip().replace("\n", " ")[:80]
        run_tool("sum_result", "要約", summary, contents, temperature=0.3)

    show_result("sum_result", "summary")
