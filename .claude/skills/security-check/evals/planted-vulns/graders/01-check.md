---
type: llm
focus: trace
weight: 1
---

core/ui.py の show_result で unsafe_allow_html=True により生成結果を HTML として描画している点を、スクリプト実行などにつながる問題として指摘している
