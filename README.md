# htmx-chat

HTMX + FastAPI + LangChain で構築したチャットアプリ。Gemini モデルをバックエンドに使用する。

## 技術スタック

- **バックエンド**: FastAPI + LangChain (`langchain`, `langchain-google-genai`)
- **AI モデル**: Google Gemini（`gemini-2.5-flash` デフォルト）
- **認証**: itsdangerous による署名付きセッショントークン（Cookie）
- **フロントエンド**: HTMX + Alpine.js + TailwindCSS + DaisyUI
- **パッケージ管理**: uv

## セットアップ

### 1. 依存パッケージのインストール

```bash
uv sync
```

### 2. 環境変数の設定

`.env` ファイルを作成して以下を設定:

```env
GOOGLE_API_KEY=your_api_key_here   # Google AI Studio で取得
SECRET_KEY=your_secret_key_here    # セッショントークンの署名に使用（任意の長いランダム文字列）
DEFAULT_MODEL=gemini-2.5-flash     # 省略可
```

`GOOGLE_API_KEY` は [Google AI Studio](https://aistudio.google.com/app/apikey) で取得できる。

### 3. 静的ファイルの準備

TailwindCSS のスタンドアロンバイナリを使って `app.min.css` をビルドする:

```powershell
# 一度だけビルド
.\bin\tailwindcss-windows-x64.exe -i .\app\static\css\app.css -o .\app\static\css\app.min.css

# 開発中はウォッチモードで自動再ビルド（サーバーと並行して別ターミナルで実行）
.\bin\tailwindcss-windows-x64.exe -i .\app\static\css\app.css -o .\app\static\css\app.min.css --watch
```

## 起動

```bash
uv run python run.py
```

`http://127.0.0.1:8000` でサーバーが立ち上がる（ホットリロード有効）。

本番環境では gunicorn を使用する。

## エンドポイント

| パス | メソッド | 認証 | 用途 |
|---|---|---|---|
| `/` | GET | 不要 | ログイン画面 |
| `/launch` | POST | 不要 | ログイン処理・Cookie 発行 |
| `/home` | GET | 必要 | ホーム画面 |
| `/chat-ui` | GET | 必要 | チャット UI |
| `/chat` | POST | 必要 | チャット API（JSON） |
| `/chat/form` | POST | 必要 | チャット API（フォーム、HTMX 向け） |
| `/healthz` | GET | 不要 | 死活監視 |

モデルはクエリパラメータで切り替え可能:

```
POST /chat?model_name=gemini-2.0-flash
```

## 開発コマンド

```bash
# リント
uv run ruff check .

# フォーマット
uv run ruff format .

# リント + 自動修正
uv run ruff check --fix .

# パッケージ追加
uv add <package>
```

## ディレクトリ構成

```
app/
  main.py          # FastAPI エントリポイント（create_app, lifespan, エラーハンドラ）
  core/
    config.py      # 設定管理（pydantic-settings + lru_cache）
    ai.py          # モデル生成・キャッシュ・依存関数
    auth.py        # トークン生成・検証・ログイン依存関数
    templates.py   # Jinja2 テンプレートラッパー（render ヘルパー）
  routers/
    launch.py      # ログイン画面・ログイン処理
    home.py        # ホーム画面
    chat_ui.py     # チャット UI 画面
    chat.py        # チャット API エンドポイント
  static/
    vendor/        # HTMX、Alpine.js
    css/           # app.css（ソース）、app.min.css（ビルド済み）
    js/            # chat.js
  templates/       # Jinja2 テンプレート
run.py             # ローカル開発用起動スクリプト
```
