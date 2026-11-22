"""AIライティングツール（Streamlit + Gemini API）"""

import os

import streamlit as st
from dotenv import load_dotenv

from core.gemini import list_text_models, pick_default_model
from core.ui import Settings
from tools import blog, chat, headline, mail, history, proofread, sns, summarize, translate

load_dotenv()

st.set_page_config(page_title="AIライティングツール", page_icon="✍️", layout="wide")


def sidebar_settings() -> Settings:
    with st.sidebar:
        st.header("⚙️ 設定")
        env_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        if env_key == "your-api-key-here":  # .env.example の見本値のまま
            st.warning(".env の GEMINI_API_KEY が見本の値のままです。実際のキーに書き換えて保存してください。")
            env_key = ""
        if env_key:
            st.success("API キー：.env から読み込み済み", icon="🔑")
            api_key = env_key
        else:
            api_key = st.text_input(
                "Gemini API キー", type="password", key="api_key_input",
                help="https://aistudio.google.com/apikey で取得できます。.env に保存すると毎回の入力が不要になります。",
            )

        models: list[str] = []
        if api_key:
            models = list_text_models(api_key)
            default = pick_default_model(models)
            model = st.selectbox(
                "モデル", models, index=models.index(default), key="model",
                help="選んだモデルが混雑・上限超えのときは、自動で別の Flash モデルに切り替えて生成します。",
            )
        else:
            model = ""
            st.info("API キーを入力するとモデルを選択できます。")

        temperature = st.slider(
            "創造性（temperature）", 0.0, 2.0, 0.7, 0.1, key="temperature",
            help="低いほど安定した・堅実な文章、高いほど多様で独創的な文章になります。"
                 "要約・校正・翻訳はツール側で低めの値を使います。",
        )
    return Settings(api_key=api_key, model=model, temperature=temperature, available_models=models)


def keep_inputs_across_pages() -> None:
    """ページ移動しても各ツールの入力内容が消えないように保持する。

    Streamlit は表示されていないページのウィジェット値を破棄するため、
    毎回の実行時に値を代入し直して保持する。
    """
    prefixes = ("blog_", "mail_", "sum_", "pr_", "tr_", "sns_", "hl_")
    skip_suffixes = ("_dl", "_clear")  # ボタン類は代入できないので除外
    for key in list(st.session_state.keys()):
        if key.startswith(prefixes) and not key.endswith(skip_suffixes) and key != "sum_file":
            st.session_state[key] = st.session_state[key]


keep_inputs_across_pages()
st.session_state["settings"] = sidebar_settings()

pages = {
    "ライティング": [
        st.Page(blog.render, title="ブログ記事作成", icon="📝", url_path="blog", default=True),
        st.Page(mail.render, title="メール作成", icon="✉️", url_path="email"),
        st.Page(summarize.render, title="要約", icon="📄", url_path="summarize"),
        st.Page(proofread.render, title="校正・リライト", icon="✏️", url_path="proofread"),
        st.Page(translate.render, title="翻訳", icon="🌐", url_path="translate"),
        st.Page(sns.render, title="SNS投稿作成", icon="📱", url_path="sns"),
        st.Page(headline.render, title="タイトル・コピー", icon="💡", url_path="headline"),
    ],
    "その他": [
        st.Page(chat.render, title="フリーチャット", icon="💬", url_path="chat"),
        st.Page(history.render, title="生成履歴", icon="🕘", url_path="history"),
    ],
}

st.navigation(pages, position="top").run()
