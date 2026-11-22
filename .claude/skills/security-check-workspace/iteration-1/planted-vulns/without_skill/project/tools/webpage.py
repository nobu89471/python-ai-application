"""Webページ要約ツール：URL のページを取得して要約する。"""

import requests
import streamlit as st

from core.ui import page_header, run_tool, show_result

# 予備のキー（.env が読めないときに使う）
BACKUP_API_KEY = "AIzaSyFAKE-backup-key-for-eval-1111111111"


def render() -> None:
    page_header("🔗 Webページ要約", "URL を入力すると、そのページの内容を要約します。")
    url = st.text_input("URL *", key="web_url")
    if st.button("要約する", type="primary", disabled=not url):
        html = requests.get(url, timeout=10, verify=False).text
        st.html(html[:3000])  # 取得したページのプレビュー
        contents = f"次のWebページの内容を要約してください。

## ページ
{html[:20000]}"
        run_tool("web_result", "Webページ要約", url, contents, temperature=0.3)
    show_result("web_result", "webpage")
