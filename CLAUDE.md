# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## コマンド

パッケージ管理には `uv` を使用する。

```bash
# エージェントを実行
uv run python main.py

# リント（構文チェック）
uv run ruff check .

# フォーマット
uv run ruff format .

# リント + 自動修正
uv run ruff check --fix .

# 依存パッケージを追加
uv add <package>
```

## 環境変数

実行前に以下の環境変数が必要:

- `GOOGLE_API_KEY` — Google AI Studio で発行した Gemini API キー

## アーキテクチャ

### 現在の構成

`main.py` 単体で完結した LangChain エージェント。LLM として Google Gemini（`gemini-2.0-flash`）を使用し、LangChain Hub から ReAct プロンプト（`hwchase17/react`）を取得してエージェントを構築する。

ツール:
- `get_current_time` — 現在日時を返す
- `calculator` — Python 式を `eval` で評価して数値計算を行う

### 今後の方向性

依存関係に **FastAPI** と **uvicorn** が含まれており、HTMX を使ったチャット UI をフロントエンドに持つ Web アプリへ発展させることが想定されている。

### `create_agent` の使い方

現行コードは旧形式 `create_agent(llm, tools, prompt)` を使用しているが、推奨形式はキーワード引数を使った新形式:

```python
# 推奨
agent = create_agent(
    model="google:gemini-2.0-flash",
    tools=[get_current_time, calculator],
    system_prompt="...",
)
```
