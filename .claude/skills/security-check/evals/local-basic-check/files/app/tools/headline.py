"""タイトル・キャッチコピー作成ツール。"""

import streamlit as st

from core.ui import extra_instructions_input, optional_line, page_header, run_tool, show_result

TYPES = ["ブログ・記事タイトル", "キャッチコピー", "メールの件名", "YouTube動画タイトル", "商品・サービス名", "プレゼン資料のタイトル"]


def render() -> None:
    page_header("💡 タイトル・キャッチコピー", "記事タイトル・キャッチコピー・件名などのアイデアをまとめて出します。")

    content = st.text_area("内容・特徴 *", key="hl_content", height=150,
                           placeholder="例：忙しい社会人向けの、10分でできる作り置きレシピ集")
    col1, col2 = st.columns(2)
    kind = col1.selectbox("種類", TYPES, key="hl_kind")
    count = col2.slider("案の数", 5, 20, 10, key="hl_count")
    target = st.text_input("ターゲット（任意）", key="hl_target", placeholder="例：20〜30代の共働き夫婦")
    extra = extra_instructions_input("hl_extra")

    if st.button("💡 アイデアを出す", type="primary", disabled=not content.strip()):
        prompt = (
            f"次の内容について「{kind}」の案を{count}個作成してください。\n\n"
            "## 条件\n"
            + optional_line("ターゲット", target)
            + optional_line("追加の指示", extra)
            + "- 数字を使う・問いかける・ベネフィットを示す・意外性を出す など、切り口を幅広く\n"
            "- 番号付きリストで出力し、各案の後ろに（ ）で狙いを短く添える\n"
            "- 最後に「## おすすめ」として、特におすすめの3案とその理由を書く\n"
            f"\n## 内容\n{content}"
        )
        run_tool("hl_result", f"タイトル・キャッチコピー（{kind}）", content.strip().replace("\n", " ")[:80],
                 prompt, temperature=1.0)

    show_result("hl_result", "headline")
