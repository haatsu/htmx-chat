# プロジェクト概要

## スタック

| レイヤー | 技術 |
|---|---|
| バックエンド | FastAPI（Python） |
| AIエージェント | LangChain `create_agent()` + Gemini（`langchain-google-genai`） |
| テンプレート | Jinja2（FastAPI の `TemplateResponse`） |
| フロントエンド | HTMX + Alpine.js + TailwindCSS + DaisyUI |
| ストリーミング | Fetch API（JS）＋ Server-Sent Events |

## 画面一覧

| 画面 | パス | 説明 |
|---|---|---|
| ログイン | `/` | ユーザ名入力・ログインのみ |
| ホーム | `/home` | アプリタイトル＋チャットへの導線 |
| チャット | `/chat-ui` | AIとの会話画面 |

※ `/chat`・`/chat/form` は既存のAPI用パスのため、画面のパスは `/chat-ui` を使う。

## 追加するディレクトリ構成

```
app/
  core/
    auth.py          # 認証依存関数・RequiresLoginException（新規）
    templates.py     # Jinja2Templates + render()ヘルパー（新規）
  routers/
    launch.py        # GET / （ログイン画面）・POST /launch（認証）
    home.py          # GET /home
    chat_ui.py       # GET /chat-ui
    chat.py          # 既存（/chat, /chat/form）＋ POST /chat/stream を追加
  templates/
    _base.html       # bare HTML shell（html/head/body）継承元
    _app_layout.html # _base.html を継承、サイドバー＋<main id="main">を追加
    _partial_base.html  # HTMXパーシャル用（bodyブロックのみ）
    errors/
      404.html       # 404エラーページ
      500.html       # 500エラーページ
    login.html       # ログイン画面（_base.html 継承）
    home.html        # ホーム画面（_app_layout.html or _partial_base.html 継承）
    chat_ui.html     # チャット画面（_app_layout.html or _partial_base.html 継承）
    _sidebar.html    # サイドバーコンポーネント（includeで使う）
  static/
    js/
      chat.js        # チャット画面専用JS（ストリーミング実装）
```

## 認証方式

**ステートレス署名トークン方式**（サーバー側にセッションストアを持たない）

- ログイン時に `username` を `SECRET_KEY` で署名したトークンを生成し、`session_token` クッキー（HttpOnly）にセット
- トークン自体にユーザ名と有効期限が含まれる（`itsdangerous.URLSafeTimedSerializer` を使用）
- リクエスト時はクッキーのトークンを検証してユーザ名を取り出す。サーバー側にセッション保存は不要
- ホーム・チャット画面はFastAPI依存関数 `get_current_user` で認証チェックし、未認証なら `/` にリダイレクト

**必要な環境変数**: `SECRET_KEY`（任意の長い乱数文字列）

## 制約・方針

- SSE は GET のみ対応・HTMX は Fetch API 非対応のため、チャットのストリーミング送受信は **JS（Fetch API）で実装する**
- その他の画面遷移・フォーム送信は HTMX を使う
- Jinja2 テンプレートを使うため `uv add jinja2 itsdangerous` で追加する（`python-multipart` は既存依存）
- `app/static` 配下のベンダーファイル（HTMX・Alpine.js）とCSSをテンプレートから参照するため、`main.py` の Static ファイルマウントを有効化する:
  ```python
  app.mount("/static", StaticFiles(directory="app/static"), name="static")
  ```
  （現在コメントアウトされているので外す）
