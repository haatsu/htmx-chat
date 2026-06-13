# 画面仕様

## 共通：サイドバー（`_sidebar.html`）

ホーム・チャット画面の両方で `{% include "_sidebar.html" %}` として使う。

**要素**:
- アプリ名（テキストロゴ）
- ナビゲーションリンク
  - 「ホーム」→ `/home`
  - 「チャット」→ `/chat-ui`
- 現在のページをアクティブ状態でハイライト（テンプレート変数 `active_page` で判定）
  - `active_page="home"` or `active_page="chat"`

**レイアウト**:
- 画面左側に固定表示（`fixed` または `sticky`）
- 幅は `w-64` 程度

---

## ホーム画面（`GET /home`）

**ファイル**: `app/routers/home.py`、`app/templates/home.html`

**認証**: `get_current_user` 依存関数で必須

**エンドポイント**:
```python
@router.get("/home")
async def home(request: Request, username: str = Depends(get_current_user)):
    return TemplateResponse("home.html", {"request": request, "username": username, "active_page": "home"})
```

**画面レイアウト**:
- サイドバー（左）＋ メインコンテンツ（右）の2カラム
- メインコンテンツ：
  - アプリタイトル（大見出し）
  - ウェルカムメッセージ（「こんにちは、{username} さん」など）
  - 「チャットを始める」ボタン → `/chat-ui` へのリンク（`<a>` タグ、HTMXなし）

---

## チャット画面（`GET /chat-ui`）

**ファイル**: `app/routers/home.py` または `app/routers/chat.py` に追加、`app/templates/chat_ui.html`

**認証**: `get_current_user` 依存関数で必須

**エンドポイント**:
```python
@router.get("/chat-ui")
async def chat_ui(request: Request, username: str = Depends(get_current_user)):
    return TemplateResponse("chat_ui.html", {
        "request": request,
        "username": username,
        "active_page": "chat",
        "thread_id": request.cookies.get("session_token"),  # スレッドIDはセッショントークンを流用
    })
```

**画面レイアウト**:
```
┌──────────┬─────────────────────────────────┐
│          │  メッセージ表示エリア（scroll）  │
│ サイドバー│                                 │
│          │                                 │
│          ├─────────────────────────────────┤
│          │  入力フォームエリア              │
└──────────┴─────────────────────────────────┘
```

**メッセージ表示エリア**:
- ID: `#messages`
- overflow-y: auto でスクロール
- 新しいメッセージが追加されたら自動スクロール（JS: `el.scrollTop = el.scrollHeight`）
- ユーザーメッセージ：右寄せバブル
- アシスタントメッセージ：左寄せバブル
- ストリーミング中はアシスタントバブルが逐次更新される

**入力フォームエリア**:
- 画面下部に固定
- `<textarea id="chat-input">`:
  - `rows="1"` 初期値
  - `style="resize: none; overflow: hidden;"` で手動リサイズ禁止
  - 入力内容に応じて高さが自動拡張（JS: `input.style.height = 'auto'; input.style.height = input.scrollHeight + 'px'`）
  - **Enter** → 送信（デフォルトの改行を preventDefault）
  - **Shift+Enter** → 改行（通常動作、送信しない）
  - 送信中は disabled にする
- 「送信」ボタン（`id="send-btn"`）：
  - クリックでも送信
  - ストリーミング中は disabled

**JS の責務**（詳細は `chat-streaming.md` 参照）:
- Enter キーハンドリング
- テキストエリア自動拡張
- チャット送信（Fetch POST）
- SSE ストリーム読み取り＆DOM更新
