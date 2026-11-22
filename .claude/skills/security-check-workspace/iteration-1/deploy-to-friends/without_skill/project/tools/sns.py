"""SNS投稿作成ツール。"""

import streamlit as st

from core.ui import extra_instructions_input, optional_line, page_header, run_tool, show_result

PLATFORMS = {
    "X（旧Twitter）": "全角140字以内。冒頭で興味を引き、改行を活用する",
    "Instagram": "キャプションとして、改行と絵文字で読みやすく。最後にハッシュタグをまとめる",
    "Threads": "500字以内。会話のような親しみやすい語り口",
    "LinkedIn": "ビジネス向け。学びや気づきを中心に、プロフェッショナルな語り口",
    "Facebook": "近況報告のような自然な文章",
    "note / ブログ告知": "記事を読みたくなる紹介文。記事の価値が伝わるように",
}
TONES = ["親しみやすい", "プロフェッショナル", "ユーモラス", "エモーショナル", "情報重視・簡潔"]


def render() -> None:
    page_header("📱 SNS投稿作成", "伝えたい内容から、各SNSに最適化した投稿文を作成します。")

    content = st.text_area("投稿したい内容 *", key="sns_content", height=150,
                           placeholder="例：新しいブログ記事「在宅ワークで集中力を保つコツ」を公開した")
    col1, col2 = st.columns(2)
    platform = col1.selectbox("プラットフォーム", list(PLATFORMS), key="sns_platform")
    tone = col2.selectbox("トーン", TONES, key="sns_tone")
    col1, col2, col3 = st.columns(3)
    count = col1.number_input("案の数", 1, 5, 3, key="sns_count")
    use_hashtag = col2.checkbox("ハッシュタグを付ける", value=True, key="sns_hashtag")
    use_emoji = col3.checkbox("絵文字を使う", value=True, key="sns_emoji")
    extra = extra_instructions_input("sns_extra")

    if st.button("📱 投稿文を作成", type="primary", disabled=not content.strip()):
        prompt = (
            f"次の内容について、{platform}向けの投稿文を{count}案作成してください。\n\n"
            "## 条件\n"
            f"- プラットフォームの特性：{PLATFORMS[platform]}\n"
            f"- トーン：{tone}\n"
            f"- ハッシュタグ：{'適切なものを付ける' if use_hashtag else '付けない'}\n"
            f"- 絵文字：{'適度に使う' if use_emoji else '使わない'}\n"
            + optional_line("追加の指示", extra)
            + "- 各案は「## 案1」のように見出しで区切り、切り口が異なるようにする\n"
            f"\n## 投稿したい内容\n{content}"
        )
        run_tool("sns_result", f"SNS投稿（{platform}）", content.strip().replace("\n", " ")[:80], prompt)

    show_result("sns_result", "sns")
