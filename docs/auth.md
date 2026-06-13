# 認証フロー

## ログイン画面（`GET /`）

- `app/templates/login.html` をレンダリングする
- ページ中央にカードを配置し、以下の要素を含む：
  - アプリタイトル（見出し）
  - ユーザ名テキスト入力（`name="username"`, プレースホルダー「名前を入力」）
  - ログインボタン
- フォームは HTMX を使わず、通常の HTML フォームで `POST /launch` に送信する
  ```html
  <form method="post" action="/launch">
    <input type="text" name="username" required placeholder="名前を入力" />
    <button type="submit">ログイン</button>
  </form>
  ```

## ログインエンドポイント（`POST /launch`）

**ファイル**: `app/routers/launch.py`

**リクエスト**: `application/x-www-form-urlencoded`
- `username: str`（必須・空文字不可）

**処理**:
1. `uuid.uuid4()` でトークンを生成
2. `request.app.state.sessions[token] = username` でインメモリ保存
3. レスポンスに `session_token=<token>` クッキーをセット
   - `httponly=True`
   - `samesite="lax"`
   - `max_age=86400`（24時間）
4. `/home` へ 303 リダイレクト

**実装例**:
```python
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
import uuid

router = APIRouter()

@router.post("/launch")
async def launch(request: Request, username: str = Form(..., min_length=1)):
    token = str(uuid.uuid4())
    request.app.state.sessions[token] = username
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie("session_token", token, httponly=True, samesite="lax", max_age=86400)
    return response
```

## 認証依存関数

**ファイル**: `app/core/auth.py`（新規作成）

```python
from fastapi import Request
from fastapi.responses import RedirectResponse

def get_current_user(request: Request) -> str:
    token = request.cookies.get("session_token")
    if token:
        username = request.app.state.sessions.get(token)
        if username:
            return username
    # 未認証はログインへリダイレクト
    raise RedirectResponse(url="/")
```

※ `raise RedirectResponse(...)` は FastAPI の例外ハンドラで 302 を返す。  
あるいは `HTTPException(status_code=303)` ＋ `headers={"Location": "/"}` でも可。

## `app.state` の初期化

`app/main.py` の `lifespan` に追加:

```python
app.state.sessions = {}  # token -> username
```

## ルーターの登録

`app/main.py` で `launch.router` と `home.router` を `include_router` する。
