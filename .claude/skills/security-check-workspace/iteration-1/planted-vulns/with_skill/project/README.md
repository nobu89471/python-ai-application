# ✍️ AIライティングツール

Python + Streamlit + Gemini API で作った、個人用のオールインワン AI ライティングツールです。

## 機能

| ツール | 内容 |
| --- | --- |
| 📝 ブログ記事作成 | テーマ → **構成案（編集可）** → 本文 の2ステップ。構成なしで一気に書くことも可能 |
| ✉️ メール作成 | 受信メールへの返信／新規メール。返信方針・相手との関係・トーン・複数パターン指定 |
| 📄 要約 | テキスト貼り付け or ファイル（txt / md / **PDF**）。3行・箇条書き・構造化レポートなど |
| ✏️ 校正・リライト | 誤字脱字チェック（修正箇所の表つき）、敬語化、簡潔化、膨らませる など |
| 🌐 翻訳 | 10言語・スタイル指定、訳し方の解説オプション |
| 📱 SNS投稿作成 | X / Instagram / Threads / LinkedIn などに最適化した投稿案 |
| 💡 タイトル・コピー | 記事タイトル・キャッチコピー・件名などのアイデア出し |
| 💬 フリーチャット | 文章の相談を対話形式で |
| 🕘 生成履歴 | セッション中の生成結果を一覧・まとめてダウンロード |

全ツール共通：ストリーミング表示 / コピー用テキスト / Markdown ダウンロード / モデル・創造性（temperature）の切り替え

## セットアップ

> ⚠️ このPCの `python` コマンドは Anaconda の Python 3.8 を指しています。
> Gemini SDK は Python 3.9 以上が必要なため、`py -3.14` で作った仮想環境（`.venv`）を使ってください。

```powershell
# 1. 仮想環境（作成済みの場合は不要）
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# 2. API キーの設定（https://aistudio.google.com/apikey で取得）
copy .env.example .env
#   → .env を開いて GEMINI_API_KEY=... を書き換える
#   （.env を使わず、起動後にサイドバーで入力してもOK）

# 3. 起動
.venv\Scripts\python -m streamlit run app.py
```

ブラウザで http://localhost:8501 が開きます。

## ファイル構成

```
app.py              # エントリーポイント（サイドバー設定・ページ切り替え）
core/
  gemini.py         # Gemini API 呼び出し（ストリーミング・モデル一覧取得）
  ui.py             # 共通UI（生成・結果表示・履歴）とベースのシステムプロンプト
tools/              # 各ツール（1ファイル = 1ページ）
  blog.py  mail.py  summarize.py  proofread.py
  translate.py  sns.py  headline.py  chat.py  history.py
```

## ツールの追加方法

1. `tools/` に新しいファイルを作り、`render()` 関数を定義する（`tools/headline.py` が短くて参考になります）
2. プロンプトを組み立てて `run_tool(結果キー, ツール名, 履歴用の要約, プロンプト)` を呼び、`show_result(結果キー, ファイル名)` で表示
3. `app.py` の `pages` に `st.Page(...)` を追加
4. 入力内容をページ移動後も残したい場合は、ウィジェットの key の接頭辞を `app.py` の `keep_inputs_across_pages()` に追加
