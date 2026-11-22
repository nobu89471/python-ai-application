"""翻訳ツール。"""

import streamlit as st

from core.ui import optional_line, page_header, run_tool, show_result

LANGUAGES = ["英語", "日本語", "中国語（簡体字）", "中国語（繁体字）", "韓国語", "スペイン語", "フランス語", "ドイツ語", "ポルトガル語", "ベトナム語"]
STYLES = {
    "自然な意訳": "ネイティブが書いたような自然な表現を優先して意訳する",
    "直訳寄り": "原文の構造と意味をできるだけ忠実に保って訳す",
    "ビジネス文書": "ビジネス文書にふさわしいフォーマルな表現で訳す",
    "カジュアル": "会話やSNSで使うようなくだけた表現で訳す",
}


def render() -> None:
    page_header("🌐 翻訳", "文脈を踏まえた自然な翻訳を行います。原文の言語は自動判定します。")

    text = st.text_area("原文 *", key="tr_text", height=240)
    col1, col2 = st.columns(2)
    lang = col1.selectbox("翻訳先の言語", LANGUAGES, key="tr_lang")
    style = col2.selectbox("翻訳スタイル", list(STYLES), key="tr_style")
    context = st.text_input("文脈・用途（任意）", key="tr_context", placeholder="例：海外の取引先へのメール／技術ドキュメント")
    explain = st.checkbox("訳し方のポイント（注意した表現など）も解説する", key="tr_explain")

    if st.button("🌐 翻訳する", type="primary", disabled=not text.strip()):
        prompt = (
            f"次の文章を{lang}に翻訳してください。\n\n"
            "## 条件\n"
            f"- スタイル：{STYLES[style]}\n"
            + optional_line("文脈・用途", context)
            + "- 固有名詞・数値・URLは正確に保つ\n"
            + ("- 翻訳文のあとに「## 翻訳のポイント」として、訳し分けた表現や注意点を箇条書きで解説する（解説は日本語）\n"
               if explain else "- 翻訳文のみを出力する\n")
            + f"\n## 原文\n{text}"
        )
        run_tool("tr_result", f"翻訳（→{lang}）", text.strip().replace("\n", " ")[:80], prompt, temperature=0.3)

    show_result("tr_result", "translation")
