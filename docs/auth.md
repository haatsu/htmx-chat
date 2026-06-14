# 認証フロー

## 設計方針

ユーザ名を `SECRET_KEY` で署名したトークンをクッキーに保存する**ステートレス方式**。  
サーバー側にセッションストア（`app.state.sessions` 等）は持たない。

```
ログイン → username を SECRET_KEY で署名 → トークンをクッキーにセット
リクエスト → クッキーのトークンを検証 → username を取り出す
```

ライブラリ: `itsdangerous.URLSafeTimedSerializer`（`uv add itsdangerous`）

---

## 環境変数

`app/core/config.py` に追加:

```python
class Settings(BaseSettings):
    google_api_key: str
    default_model: str = "gemini-2.5-flash"
    secret_key: str  # トークン署名用。openssl rand -hex 32 などで生成
```

`.env` に追加:
```
SECRET_KEY=<長い乱数文字列>
```

---

## トークンのユーティリティ

**ファイル**: `app/core/auth.py`（新規作成）

```python
from fastapi import Request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.core.config import get_settings

TOKEN_MAX_AGE = 86400  # 24時間

class RequiresLoginException(Exception):
    pass

def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key)

def create_token(username: str) -> str:
    """username を署名してトークンを返す。"""
    return _serializer().dumps({"username": username})

def decode_token(token: str) -> str | None:
    """トークンを検証して username を返す。無効・期限切れは None。"""
    try:
        data = _serializer().loads(token, max_age=TOKEN_MAX_AGE)
        return data["username"]
    except (BadSignature, SignatureExpired, KeyError):
        return None

def get_current_user(request: Request) -> str:
    """認証済みユーザのユーザ名を返す依存関数。未認証は RequiresLoginException を raise。"""
    token = request.cookies.get("session_token")
    if token:
        username = decode_token(token)
        if username:
            request.state.user = username  # render() から参照するためにセット
            return username
    raise RequiresLoginException()
```

---

## Jinja2Templates の共有インスタンス

**ファイル**: `app/core/templates.py`（新規作成）

```python
from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

def render(request: Request, template_name: str, context: dict = {}) -> templates.TemplateResponse:
    """username・hx_request を自動付与してテンプレートをレンダリングする。"""
    base = {
        "request": request,
        "username": getattr(request.state, "user", None),
        "hx_request": request.headers.get("HX-Request") == "true",
    }
    return templates.TemplateResponse(template_name, {**base, **context})
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
1. `create_token(username)` で署名済みトークンを生成
2. レスポンスに `session_token=<token>` クッキーをセット
   - `httponly=True`
   - `samesite="lax"`
   - `max_age=86400`（24時間）
3. `/home` へ 303 リダイレクト

**実装**:

```python
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.auth import create_token
from app.core.templates import templates

router = APIRouter()

@router.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/launch")
async def launch(username: str = Form(..., min_length=1)):
    token = create_token(username)
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie("session_token", token, httponly=True, samesite="lax", max_age=86400)
    return response
```

---

## `app/main.py` への追加事項

### `lifespan` について

`app.state.sessions` の初期化は**不要**（ステートレス方式のため）。

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
from app.routers import launch, home, chat_ui, chat

app.include_router(launch.router)
app.include_router(home.router)
app.include_router(chat_ui.router)
app.include_router(chat.router)
```
