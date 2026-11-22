"""ブログ記事作成ツール：構成案 → 本文 の2ステップで記事を書く。"""

import streamlit as st

from core.ui import (
    extra_instructions_input,
    generate,
    add_history,
    optional_line,
    page_header,
    show_result,
)

TONES = ["親しみやすい", "専門的・論理的", "カジュアル", "丁寧・フォーマル", "熱量高め・エモーショナル"]


def _brief() -> str:
    s = st.session_state
    return (
        f"- テーマ：{s.blog_theme}\n"
        + optional_line("想定読者", s.blog_reader)
        + optional_line("SEOキーワード", s.blog_keywords)
        + f"- 文体・トーン：{s.blog_tone}\n"
        + f"- 文字数の目安：約{s.blog_length:,}字\n"
        + optional_line("追加の指示", s.blog_extra)
    )


def render() -> None:
    page_header("📝 ブログ記事作成", "テーマから構成案を作り、編集してから本文を書き上げます。")

    st.text_input("テーマ・書きたい内容 *", key="blog_theme",
                  placeholder="例：在宅ワークで集中力を保つ5つのコツ")
    col1, col2 = st.columns(2)
    col1.text_input("想定読者", key="blog_reader", placeholder="例：在宅勤務を始めたばかりの会社員")
    col2.text_input("SEOキーワード（カンマ区切り）", key="blog_keywords", placeholder="例：在宅ワーク, 集中力")
    col1, col2 = st.columns(2)
    col1.selectbox("文体・トーン", TONES, key="blog_tone")
    col2.slider("文字数の目安", 800, 8000, 3000, step=200, key="blog_length")
    extra_instructions_input("blog_extra")

    ready = bool(st.session_state.blog_theme.strip())

    # ---- STEP 1: 構成案 ----
    st.subheader("STEP 1　構成案")
    c1, c2 = st.columns(2)
    make_outline = c1.button("🧩 構成案を作成", type="primary", disabled=not ready, width="stretch")
    direct = c2.button("⚡ 構成なしで本文を一気に書く", disabled=not ready, width="stretch")

    if make_outline:
        prompt = (
            "以下の条件でブログ記事の構成案を作成してください。\n\n"
            f"{_brief()}\n"
            "## 出力形式（Markdown）\n"
            "1. タイトル案を3つ（読者がクリックしたくなるもの）\n"
            "2. 記事の狙い（読者の悩みと、読後に得られること）を2〜3行\n"
            "3. 見出し構成：H2（##）とH3（###）で構成し、各見出しの下に書く要点を箇条書きで1〜3個\n"
            "導入とまとめの見出しも含めてください。"
        )
        outline = generate(prompt)
        if outline:
            st.session_state.blog_outline = outline

    if "blog_outline" in st.session_state:
        st.text_area("構成案（自由に編集できます）", key="blog_outline", height=350)

    # ---- STEP 2: 本文 ----
    has_outline = bool(st.session_state.get("blog_outline", "").strip())
    if has_outline:
        st.subheader("STEP 2　本文")
        write_body = st.button("✍️ この構成で本文を書く", type="primary", disabled=not ready)
    else:
        write_body = False

    if write_body or direct:
        outline_part = (
            f"## 構成案（この構成に沿って書くこと。タイトルは案から最適なものを1つ選ぶ）\n"
            f"{st.session_state.blog_outline}\n\n"
            if write_body else ""
        )
        prompt = (
            "以下の条件でブログ記事の本文を執筆してください。\n\n"
            f"## 条件\n{_brief()}\n"
            f"{outline_part}"
            "## 執筆ルール\n"
            "- Markdown形式で、先頭に「# タイトル」を書く\n"
            "- 見出し（##, ###）を使い、1段落は2〜4文程度で読みやすく\n"
            "- 具体例・体験談風のエピソード・数字などを交えて説得力を持たせる\n"
            "- SEOキーワードがあれば、不自然にならない範囲でタイトル・見出し・本文に含める\n"
            "- 最後にまとめと、読者への一言を入れる"
        )
        body = generate(prompt)
        if body:
            st.session_state.blog_result = body
            add_history("ブログ記事作成", st.session_state.blog_theme, body)

    show_result("blog_result", "blog")
