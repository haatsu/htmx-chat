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
  routers/
    launch.py        # ログイン・認証エンドポイント
    home.py          # ホーム画面エンドポイント
    chat.py          # 既存（/chat, /chat/form）＋ /chat/stream を追加
  templates/
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
- Jinja2 テンプレートを使うため、`python-multipart` は既存依存、`jinja2` を `uv add jinja2` で追加する
