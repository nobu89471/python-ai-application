"""メール作成ツール：受信メールへの返信、または新規メールを作成する。"""

import streamlit as st

from core.ui import extra_instructions_input, optional_line, page_header, run_tool, show_result

RELATIONS = ["社外（取引先・顧客）", "社内（上司）", "社内（同僚・部下）", "友人・知人", "初めての相手"]
TONES = ["丁寧・ビジネス標準", "とても丁寧（かしこまった）", "やわらかく丁寧", "カジュアル", "簡潔・要点のみ"]
STANCES = ["おまかせ（内容に合わせて）", "承諾する", "お断りする", "質問・確認する", "お礼を伝える", "お詫びする", "日程を調整する"]


def render() -> None:
    page_header("✉️ メール作成", "受信したメールへの返信文や、新しいメールの文面を作成します。")

    mode = st.radio("作成モード", ["返信メール", "新規メール"], horizontal=True, key="mail_mode")

    if mode == "返信メール":
        received = st.text_area("受信したメール本文 *", key="mail_received", height=220,
                                placeholder="返信したいメールをここに貼り付けてください")
        stance = st.selectbox("返信の方針", STANCES, key="mail_stance")
    else:
        received = ""
        stance = ""

    points = st.text_area(
        "伝えたい要点" + ("（任意）" if mode == "返信メール" else " *"),
        key="mail_points", height=100,
        placeholder="例：来週火曜の14時なら参加可能／資料は金曜までに送る",
    )
    col1, col2 = st.columns(2)
    relation = col1.selectbox("相手との関係", RELATIONS, key="mail_relation")
    tone = col2.selectbox("トーン", TONES, key="mail_tone")
    col1, col2 = st.columns(2)
    sender = col1.text_input("差出人名（署名用・任意）", key="mail_sender", placeholder="例：山田")
    variations = col2.number_input("作成するパターン数", 1, 3, 1, key="mail_variations")
    extra = extra_instructions_input("mail_extra")

    required = received if mode == "返信メール" else points
    if st.button("✉️ メールを作成", type="primary", disabled=not required.strip()):
        conditions = (
            f"- 相手との関係：{relation}\n"
            f"- トーン：{tone}\n"
            + (f"- 返信の方針：{stance}\n" if stance else "")
            + optional_line("伝えたい要点", points)
            + optional_line("差出人名", sender)
            + optional_line("追加の指示", extra)
        )
        if mode == "返信メール":
            task = f"以下の受信メールに対する返信メールを作成してください。\n\n## 受信メール\n{received}\n\n"
        else:
            task = "以下の条件で新規メールを作成してください。\n\n"
        prompt = (
            f"{task}## 条件\n{conditions}\n"
            "## 出力ルール\n"
            "- 「件名：」の行と本文を出力する（返信の場合の件名は「Re: 元の件名」を基本とする）\n"
            "- 日本のビジネスメールの慣習（宛名・挨拶・結び）に沿う。ただしカジュアル指定時は簡略化してよい\n"
            "- 不明な固有名詞・日時は【　】で囲んだプレースホルダーにする\n"
            f"- {variations}パターン作成し、複数の場合は「## パターン1」のように見出しで区切り、それぞれ方向性を一言添える"
        )
        summary = (received or points).strip().replace("\n", " ")[:80]
        run_tool("mail_result", "メール作成", summary, prompt)

    show_result("mail_result", "email")
