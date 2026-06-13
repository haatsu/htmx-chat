# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## コマンド

パッケージ管理には `uv` を使用する。

```bash
# 開発サーバー起動（ホットリロード有効）
uv run python run.py

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

`.env` ファイルに以下を設定する（pydantic-settings が自動で読み込む）:

- `GOOGLE_API_KEY` — Google AI Studio で発行した Gemini API キー
- `DEFAULT_MODEL` — 省略時は `gemini-2.5-flash`

## アーキテクチャ

### ディレクトリ構成

```
app/
  main.py          # FastAPI アプリのエントリポイント（create_app）
  core/
    config.py      # 設定管理（pydantic-settings + lru_cache）
    ai.py          # モデル生成・キャッシュ・依存関数
  routers/
    chat.py        # チャットエンドポイント
  static/
    vendor/        # HTMX、Alpine.js（ベンダーファイル）
    css/           # TailwindCSS、DaisyUI
run.py             # ローカル開発用起動スクリプト（本番は gunicorn）
```

### モデルのライフサイクル

起動時に `lifespan`（`app/main.py`）でデフォルトモデルを初期化し `app.state.models` に格納する。  
`get_model`（`app/core/ai.py`）が依存関数として各エンドポイントにモデルを渡す。  
未キャッシュのモデル名が指定された場合は初回リクエスト時に初期化してキャッシュする。

```python
# ルーターでの使い方
from app.core.ai import get_model

@router.post("/example")
async def example(model=Depends(get_model)):
    agent = create_agent(model=model, ...)
```

モデル切替はクエリパラメータで行う:

```
POST /chat?model_name=gemini-2.0-flash
```

### エンドポイント

| パス | メソッド | 形式 | 用途 |
|---|---|---|---|
| `/chat` | POST | JSON (`{"message": "..."}`) | APIクライアント向け |
| `/chat/form` | POST | Form (`message=...`) | HTMX向け（デフォルト形式） |
| `/healthz` | GET | — | 死活監視 |

### フロントエンド

HTMX + Alpine.js + TailwindCSS + DaisyUI を使用。  
HTMX はデフォルトでフォーム形式（`application/x-www-form-urlencoded`）で送信するため、`/chat/form` を使う。  
JSONで送る場合は `hx-ext="json-enc"` が必要。

### `create_agent` の使い方

```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,  # init_chat_model が返すインスタンス
    tools=[get_current_time, calculator],
    system_prompt="You are a helpful assistant. Answer in the same language as the user.",
)
```
