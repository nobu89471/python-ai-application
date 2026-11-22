# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal, single-user AI writing tool (Japanese UI) built with Streamlit + Gemini API (`google-genai` SDK). No database, no auth — all state lives in `st.session_state` and is lost on browser reload.

## Environment & commands

- **Always use `.venv\Scripts\python`.** The bare `python` on this machine is Anaconda Python 3.8, which is too old for `google-genai` (needs 3.9+). The venv was created with `py -3.14`.
- Install: `.venv\Scripts\python -m pip install -r requirements.txt`
- Run: `.venv\Scripts\python -m streamlit run app.py` (http://localhost:8501)
- API key: `GEMINI_API_KEY` in `.env` (loaded via python-dotenv), or entered in the sidebar if unset. The `.env.example` placeholder value `your-api-key-here` is deliberately treated as "unset". Key format is not necessarily `AIza…`/39 chars — don't validate on shape.
- There is no test suite or linter configured. Pages can be smoke-tested headlessly with `streamlit.testing.v1.AppTest` by injecting settings and calling a tool's `render()`:
  ```python
  AppTest.from_string('''
  import streamlit as st, importlib, core.ui as ui
  st.session_state["settings"] = ui.Settings(api_key="", model="dummy", temperature=0.7)
  importlib.import_module("tools.blog").render()
  ''').run()
  ```
  Run with `PYTHONPATH=.` and `PYTHONIOENCODING=utf-8` (Windows console is cp932 and chokes on emoji). To avoid real API calls, monkeypatch `core.gemini.stream_text`.

## Architecture

- `app.py` — entry point. Builds the sidebar (API key, model, temperature) into a `Settings` object stored at `st.session_state["settings"]`, then routes pages with `st.navigation(..., position="top")`. Each page is a plain `render()` function from `tools/`, registered via `st.Page(module.render, url_path=...)`.
- `core/gemini.py` — all Gemini SDK access. Model list is fetched live from the API (`list_text_models`, cached 1h) and filtered by `_EXCLUDE_KEYWORDS`; `pick_default_model` prefers a stable Flash model. `stream_with_fallback` tries the selected model, and if it fails with a retryable code (`RETRYABLE_CODES`: 404/429/500/503) **before any text is emitted**, moves to the next candidate. Model availability on the free tier changes often (e.g. 2.5-flash returned 404, newest flash frequently 503), which is why fallback exists — don't hardcode model names elsewhere.
- `core/ui.py` — shared tool plumbing:
  - `generate(contents, system=BASE_SYSTEM, temperature=None)` streams output into a temporary placeholder, then clears it and returns the full text (or `None` on error, after showing a Japanese error with `ERROR_HINTS`). `Settings.candidate_models()` decides the fallback order.
  - `run_tool(result_key, tool_name, summary, contents, **kw)` = generate + store in `st.session_state[result_key]` + append to history.
  - `show_result(result_key, filename)` renders the stored result (preview / copy tab / download / clear). Results are shown from session state on every rerun, which is why streaming happens in a placeholder that gets cleared — otherwise text would render twice.
  - `BASE_SYSTEM` is the default system prompt (Japanese pro writer, output only the deliverable). Tools that need precision (summarize, proofread check, translate) pass a low `temperature`; headline ideas use 1.0.
- `tools/*.py` — one page per tool. Each builds a Japanese prompt string from widgets (`optional_line()` omits empty fields) and calls `run_tool` + `show_result`. Exceptions: `blog.py` is two-step (outline stored in widget key `blog_outline`, user-editable, then body), `chat.py` keeps `chat_messages` and sends full history via `to_chat_contents`, `summarize.py` sends PDFs as `file_part(bytes, "application/pdf")` alongside the prompt.

## Conventions when adding a tool

1. Create `tools/<name>.py` with `render()`; give all widget keys a unique short prefix (e.g. `hl_`) and use `<prefix>result` as the result key.
2. Register it in `app.py`'s `pages` dict.
3. Add the prefix to `keep_inputs_across_pages()` in `app.py`. Streamlit discards widget state for pages not currently rendered; this function re-assigns those keys each run so inputs survive page switches. Keys that can't be assigned (buttons ending `_dl`/`_clear`, file uploaders like `sum_file`) must be excluded or Streamlit raises.
4. Use `width="stretch"` rather than the deprecated `use_container_width`.

UI text and prompts are in Japanese; keep new user-facing text Japanese.
