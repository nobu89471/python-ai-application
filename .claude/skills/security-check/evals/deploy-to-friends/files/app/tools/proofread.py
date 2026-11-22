"""校正・リライトツール：誤字脱字チェックや文体の書き換えを行う。"""

import streamlit as st

from core.ui import extra_instructions_input, optional_line, page_header, run_tool, show_result

MODES = {
    "誤字脱字・文法チェック": (
        "誤字脱字、文法の誤り、表記ゆれ、不自然な表現を校正してください。\n"
        "出力は次の2部構成にしてください：\n"
        "1. 「## 修正後の文章」：修正を反映した全文\n"
        "2. 「## 修正箇所」：| 修正前 | 修正後 | 理由 | の表。修正がなければ「修正箇所はありません」と書く\n"
        "文章の内容や文体は変えないでください。"
    ),
    "読みやすく整える": "意味を変えずに、一文を短くする・語順を整える・接続詞を適切にするなどして読みやすく書き直してください。",
    "より丁寧に（敬語）": "ビジネスで使える適切な敬語・丁寧な表現に書き直してください。過剰な二重敬語は避けてください。",
    "カジュアルに": "親しみやすく、くだけた自然な口語の文章に書き直してください。",
    "簡潔に短く": "要点を残したまま、冗長な表現を削って半分程度の長さに書き直してください。",
    "詳しく膨らませる": "内容を補足し、具体例や説明を加えて1.5〜2倍程度の長さに膨らませてください。事実を捏造しないよう、一般的な説明にとどめてください。",
    "説得力を高める": "論理構成を整え、根拠や具体性を補強し、読み手を納得させる文章に書き直してください。",
}


def render() -> None:
    page_header("✏️ 校正・リライト", "誤字脱字のチェックや、目的に合わせた文章の書き換えを行います。")

    text = st.text_area("対象の文章 *", key="pr_text", height=260)
    mode = st.selectbox("処理内容", list(MODES), key="pr_mode")
    target = st.text_input("読み手・用途（任意）", key="pr_target", placeholder="例：社内報告書／Webサイトの紹介文")
    extra = extra_instructions_input("pr_extra")

    if st.button("✏️ 実行", type="primary", disabled=not text.strip()):
        prompt = (
            f"{MODES[mode]}\n\n"
            + (
                "## 補足\n" + optional_line("読み手・用途", target) + optional_line("追加の指示", extra) + "\n"
                if target.strip() or extra.strip() else ""
            )
            + f"## 対象の文章\n{text}"
        )
        temperature = 0.2 if mode == "誤字脱字・文法チェック" else None
        run_tool("pr_result", f"校正・リライト（{mode}）", text.strip().replace("\n", " ")[:80],
                 prompt, temperature=temperature)

    show_result("pr_result", "rewrite")
