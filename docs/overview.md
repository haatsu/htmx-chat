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
    templates.py     # Jinja2Templates シングルトン（新規）
  routers/
    launch.py        # GET / （ログイン画面）・POST /launch（認証）
    home.py          # GET /home・GET /chat-ui（認証済みHTML画面）
    chat.py          # 既存（/chat, /chat/form）＋ POST /chat/stream を追加
  templates/
    _base.html       # 全画面共通の<html>/<head>/CSS/JS（継承元）
    login.html       # ログイン画面
    home.html        # ホーム画面
    chat_ui.html     # チャット画面
    _sidebar.html    # サイドバー共通コンポーネント（includeで使う）
```

## 認証方式

- ログイン時に UUID トークンを発行し、`session_token` クッキー（HttpOnly）にセット
- トークン → ユーザ名のマッピングを `app.state.sessions: dict[str, str]` でインメモリ管理
- ホーム・チャット画面はFastAPI依存関数 `get_current_user` で認証チェックし、未認証なら `/` にリダイレクト

## 制約・方針

- SSE は GET のみ対応・HTMX は Fetch API 非対応のため、チャットのストリーミング送受信は **JS（Fetch API）で実装する**
- その他の画面遷移・フォーム送信は HTMX を使う
- Jinja2 テンプレートを使うため `uv add jinja2` で追加する（`python-multipart` は既存依存）
- `app/static` 配下のベンダーファイル（HTMX・Alpine.js）とCSSをテンプレートから参照するため、`main.py` の Static ファイルマウントを有効化する:
  ```python
  app.mount("/static", StaticFiles(directory="app/static"), name="static")
  ```
  （現在コメントアウトされているので外す）
