# 認証フロー

## Jinja2Templates の共有インスタンス

**ファイル**: `app/core/templates.py`（新規作成）

```python
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
```

各ルーターはここからインポートして使う:

```python
from app.core.templates import templates
```

---

## ログイン画面（`GET /`）

**ファイル**: `app/routers/launch.py`

```python
@router.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
```

**テンプレート**: `app/templates/login.html`

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

---

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

**実装**:

```python
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from app.core.templates import templates
import uuid

router = APIRouter()

@router.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/launch")
async def launch(request: Request, username: str = Form(..., min_length=1)):
    token = str(uuid.uuid4())
    request.app.state.sessions[token] = username
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie("session_token", token, httponly=True, samesite="lax", max_age=86400)
    return response
```

---

## 認証依存関数

**ファイル**: `app/core/auth.py`（新規作成）

FastAPI の依存関数から直接 `RedirectResponse` を raise しても動かないため、
カスタム例外クラスを定義し、`main.py` の `exception_handler` で処理する。

```python
from fastapi import Request

class RequiresLoginException(Exception):
    pass

def get_current_user(request: Request) -> str:
    token = request.cookies.get("session_token")
    if token:
        username = request.app.state.sessions.get(token)
        if username:
            return username
    raise RequiresLoginException()
```

---

## `app/main.py` への追加事項

### `app.state` の初期化

`lifespan` に追加:

```python
app.state.sessions = {}  # token -> username
```

### `RequiresLoginException` ハンドラの登録

```python
from fastapi.responses import RedirectResponse
from app.core.auth import RequiresLoginException

@app.exception_handler(RequiresLoginException)
async def requires_login_handler(request: Request, exc: RequiresLoginException):
    return RedirectResponse(url="/")
```

### ルーターの登録

```python
from app.routers import launch, home, chat

app.include_router(launch.router)
app.include_router(home.router)
app.include_router(chat.router)
```
