"""Streamlit + Gemini アプリ向けの簡易セキュリティスキャン（標準ライブラリのみ）。

使い方: python scan.py [プロジェクトのルート]  (省略時はカレントディレクトリ)

結果は「ヒント」であり、各ヒットは実際のコードを読んで判断すること。
秘密情報の値は表示せず、先頭数文字と長さだけを出す。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 以前
    tomllib = None

SKIP_DIRS = {
    ".venv", "venv", "env", "__pycache__", ".git", "node_modules", ".claude", ".agents",
    ".mypy_cache", ".pytest_cache", "site-packages",
}
TEXT_SUFFIXES = {
    ".py", ".toml", ".txt", ".md", ".json", ".yaml", ".yml", ".cfg", ".ini",
    ".env", ".bat", ".ps1", ".sh", ".html", ".js",
}

findings: list[tuple[str, str, str]] = []  # (区分, 場所, メッセージ)


def add(kind: str, where: str, msg: str) -> None:
    findings.append((kind, where, msg))


def mask(value: str) -> str:
    value = value.strip().strip("'\"")
    if not value:
        return "(空)"
    return f"{value[:4]}…({len(value)}文字)"


def iter_files(root: Path):
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS or part.endswith("-workspace") for part in rel.parts):
            continue
        if path.is_file() and (path.suffix.lower() in TEXT_SUFFIXES or path.name.startswith(".env")):
            yield path, rel


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# --- 1. 秘密情報 -------------------------------------------------------------

SECRET_PATTERNS = [
    ("Google API キー形式", re.compile(r"AIza[0-9A-Za-z_\-]{30,}")),
    ("秘密鍵", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("OpenAI/Anthropic 形式のキー", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{20,}")),
]
ASSIGN_PATTERN = re.compile(
    r"""(?i)\b([A-Z0-9_]*(?:api[_-]?key|secret|token|password|passwd)[A-Z0-9_]*)\s*[:=]\s*["']([^"'\s]{12,})["']"""
)
PLACEHOLDERS = {"your-api-key-here", "xxxxxxxxxxxxxxxx", "changeme"}


def check_secrets(root: Path) -> None:
    for path, rel in iter_files(root):
        if path.name.startswith(".env"):
            continue  # .env は別途キー名だけを確認する
        for lineno, line in enumerate(read(path).splitlines(), 1):
            for label, pat in SECRET_PATTERNS:
                for m in pat.finditer(line):
                    add("秘密情報", f"{rel}:{lineno}", f"{label}らしき文字列 {mask(m.group(0))}")
            for m in ASSIGN_PATTERN.finditer(line):
                if m.group(2).lower() in PLACEHOLDERS or "os.getenv" in line or "environ" in line:
                    continue
                add("秘密情報", f"{rel}:{lineno}", f"{m.group(1)} に文字列リテラルを代入 {mask(m.group(2))}")


def check_env_files(root: Path) -> None:
    for env in sorted(root.glob(".env*")):
        if not env.is_file():
            continue
        names = []
        for line in read(env).splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            names.append(f"{name.strip()}={mask(value)}")
        add("環境ファイル", env.name, "定義されている変数: " + (", ".join(names) or "(なし)"))


# --- 2. .gitignore / git 管理 ------------------------------------------------

def check_git(root: Path) -> None:
    gitignore = root / ".gitignore"
    ignored = read(gitignore).splitlines() if gitignore.exists() else []
    ignored = {l.strip().lstrip("/") for l in ignored if l.strip() and not l.startswith("#")}
    for target in (".env", ".streamlit/secrets.toml"):
        if target not in ignored and not (target == ".env" and ".env*" in ignored):
            add("gitignore", ".gitignore", f"{target} が .gitignore に含まれていない")
        else:
            add("OK", ".gitignore", f"{target} は .gitignore に含まれている")

    if not (root / ".git").exists():
        add("OK", "git", "git リポジトリではない（コミット経由の漏えいは現時点でなし）")
        return
    try:
        tracked = subprocess.run(
            ["git", "ls-files", ".env", ".streamlit/secrets.toml"],
            cwd=root, capture_output=True, text=True, timeout=30,
        ).stdout.split()
        history = subprocess.run(
            ["git", "log", "--all", "--format=%h", "--", ".env", ".streamlit/secrets.toml"],
            cwd=root, capture_output=True, text=True, timeout=30,
        ).stdout.split()
    except (OSError, subprocess.SubprocessError) as e:
        add("確認不可", "git", f"git コマンドを実行できなかった: {e}")
        return
    for t in tracked:
        add("秘密情報", t, "git で追跡されている（リポジトリに含まれる）")
    if history:
        add("秘密情報", "git 履歴", f".env / secrets.toml を含むコミットが {len(history)} 件ある（例: {history[0]}）")


# --- 3. Streamlit 設定 ---------------------------------------------------------

def check_streamlit_config(root: Path) -> None:
    cfg_path = root / ".streamlit" / "config.toml"
    cfg: dict = {}
    if cfg_path.exists():
        if tomllib is None:
            add("確認不可", str(cfg_path.relative_to(root)), "tomllib がない（Python 3.11 以上で実行してください）")
            return
        try:
            cfg = tomllib.loads(read(cfg_path))
        except tomllib.TOMLDecodeError as e:
            add("設定", ".streamlit/config.toml", f"TOML として読めない: {e}")
            return
    where = ".streamlit/config.toml"
    server = cfg.get("server", {})
    address = server.get("address")
    if not address:
        add("設定", where, "server.address が未設定 → 全インターフェース(0.0.0.0)で待ち受け。同じネットワークの他人がアクセスできる")
    elif address not in ("localhost", "127.0.0.1", "::1"):
        add("設定", where, f"server.address = {address!r}（localhost 以外で待ち受け）")
    else:
        add("OK", where, f"server.address = {address!r}（ローカルのみ）")
    if server.get("enableXsrfProtection") is False:
        add("設定", where, "server.enableXsrfProtection = false（XSRF 保護が無効）")
    if server.get("enableCORS") is False:
        add("設定", where, "server.enableCORS = false（CORS 保護が無効）")
    if "maxUploadSize" in server:
        add("情報", where, f"server.maxUploadSize = {server['maxUploadSize']} MB")
    client = cfg.get("client", {})
    if "showErrorDetails" in client:
        add("情報", where, f"client.showErrorDetails = {client['showErrorDetails']!r}")
    else:
        add("情報", where, "client.showErrorDetails が未設定（未処理例外の詳細がブラウザに表示されうる）")

    # 起動スクリプトや README で --server.address が指定されていないか
    for path, rel in iter_files(root):
        for lineno, line in enumerate(read(path).splitlines(), 1):
            if "--server.address" in line or "--server.port" in line:
                add("情報", f"{rel}:{lineno}", f"起動オプションの指定: {line.strip()[:120]}")


# --- 4. 危険なコードパターン ---------------------------------------------------

CODE_PATTERNS = [
    ("HTML 描画", re.compile(r"unsafe_allow_html\s*=\s*True"), "unsafe_allow_html=True（出力・入力を HTML として描画）"),
    ("HTML 描画", re.compile(r"\bst\.html\s*\("), "st.html()（HTML をそのまま描画）"),
    ("HTML 描画", re.compile(r"components\.(?:v1\.)?(?:html|iframe)\s*\("), "components.html/iframe"),
    ("コード実行", re.compile(r"(?<![\w.])(?:eval|exec)\s*\("), "eval/exec"),
    ("コード実行", re.compile(r"\bos\.system\s*\(|\bos\.popen\s*\("), "os.system/os.popen"),
    ("コード実行", re.compile(r"shell\s*=\s*True"), "subprocess の shell=True"),
    ("コード実行", re.compile(r"\bsubprocess\."), "subprocess の使用"),
    ("デシリアライズ", re.compile(r"\bpickle\.loads?\s*\(|\bmarshal\.loads?\s*\("), "pickle/marshal の読み込み"),
    ("デシリアライズ", re.compile(r"\byaml\.load\s*\((?!.*Loader\s*=\s*yaml\.SafeLoader)"), "yaml.load（SafeLoader なし）"),
    ("通信", re.compile(r"verify\s*=\s*False"), "TLS 証明書検証の無効化"),
    ("秘密情報の表示", re.compile(r"(?:print|logging\.\w+|logger\.\w+|st\.write|st\.text|st\.json|st\.code|st\.markdown|st\.caption|st\.info|st\.error|st\.warning|st\.success|st\.toast)\s*\([^)]*api_key"), "api_key を表示・ログ出力している可能性"),
    ("秘密情報の表示", re.compile(r"st\.(?:write|json)\s*\(\s*(?:st\.session_state|settings|get_settings\(\))\s*\)"), "session_state / Settings を丸ごと表示（API キーを含む）"),
    ("ファイル保存", re.compile(r"open\s*\([^)]*\.name"), "アップロード名などをパスに使ってファイルを開いている可能性"),
    ("LLM ツール", re.compile(r"\btools\s*=\s*\[|types\.Tool\b|FunctionDeclaration|automatic_function_calling|code_execution|url_context|google_search"), "Gemini にツール（関数呼び出し・検索など）を渡している可能性"),
    ("キャッシュ", re.compile(r"@st\.cache_(?:data|resource)"), "全セッション共有のキャッシュ（ユーザー固有データが入らないか確認）"),
]


def check_code(root: Path) -> None:
    for path, rel in iter_files(root):
        if path.suffix != ".py":
            continue
        lines = read(path).splitlines()
        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for kind, pat, msg in CODE_PATTERNS:
                if pat.search(line):
                    add(kind, f"{rel}:{lineno}", f"{msg}: {stripped[:100]}")
            if "text_input(" in line:
                call = " ".join(lines[lineno - 1:lineno + 4])  # 引数が複数行にわたる場合に備える
                label = re.search(r"text_input\(\s*[fr]?[\"']([^\"']*)", call)
                is_secret = label and re.search(r"(?i)api|キー(?!ワード)|secret|token|password|パスワード|鍵", label.group(1))
                if is_secret and "password" not in call.split(")")[0]:
                    add("秘密情報の表示", f"{rel}:{lineno}", "秘密情報の入力欄が type='password' でない可能性")


# --- 5. 依存パッケージ ---------------------------------------------------------

def check_requirements(root: Path) -> None:
    req = root / "requirements.txt"
    if not req.exists():
        add("情報", "requirements.txt", "requirements.txt がない")
        return
    for lineno, line in enumerate(read(req).splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if "==" not in line:
            add("依存", f"requirements.txt:{lineno}", f"バージョン固定なし: {line}")
    venv_py = root / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if venv_py.exists():
        r = subprocess.run([str(venv_py), "-m", "pip_audit", "--version"], capture_output=True, text=True)
        status = "導入済み" if r.returncode == 0 else "未導入"
        add("情報", ".venv", f"pip-audit は{status}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    check_secrets(root)
    check_env_files(root)
    check_git(root)
    check_streamlit_config(root)
    check_code(root)
    check_requirements(root)

    print(f"# セキュリティスキャン結果: {root}\n")
    print("※ ヒントです。各項目は該当コードを読んで判断してください。\n")
    order = ["秘密情報", "秘密情報の表示", "gitignore", "設定", "HTML 描画", "コード実行", "デシリアライズ",
             "通信", "ファイル保存", "LLM ツール", "キャッシュ", "依存", "環境ファイル", "情報", "確認不可", "OK"]
    for kind in order + sorted({k for k, _, _ in findings} - set(order)):
        items = [(w, m) for k, w, m in findings if k == kind]
        if not items:
            continue
        print(f"## {kind}")
        for where, msg in items:
            print(f"- {where} — {msg}")
        print()


if __name__ == "__main__":
    main()
