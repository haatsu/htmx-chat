# 設計パターン

## テンプレート継承階層

```
_base.html              ← bare HTML shell（html/head/body + CSS/JS import）
  ├── login.html        ← サイドバーなし
  └── _app_layout.html  ← サイドバー＋<main id="main"> を追加
        ├── home.html        ← 通常リクエスト時
        └── chat_ui.html     ← 通常リクエスト時

_partial_base.html      ← bodyブロックのみ（HTMXパーシャル用）
  ├── home.html        ← HX-Requestヘッダーがある時
  └── chat_ui.html     ← HX-Requestヘッダーがある時
```

### `_base.html`

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}htmx-chat{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/app.min.css">
  <script src="/static/vendor/alpinemin.js" defer></script>
  <script src="/static/vendor/htmx.min.js" defer></script>
  {% block scripts %}{% endblock %}
</head>
<body>
  {% block body %}{% endblock %}
</body>
</html>
```

### `_app_layout.html`

サイドバーつきの認証済みページ共通レイアウト。

```html
{% extends "_base.html" %}
{% block body %}
<div class="flex h-screen">
  {% include "_sidebar.html" %}
  <main id="main" class="flex-1 overflow-auto">
    {% block main %}{% endblock %}
  </main>
</div>
{% endblock %}
```

### `_partial_base.html`

HTMXが `#main` に差し込む断片用。`{% block main %}` だけ定義する。

```html
{% block main %}{% endblock %}
```

### 各認証済みページテンプレート

Jinja2 の動的 `extends` を使い、`hx_request` フラグで継承元を切り替える。

```html
{% extends "_app_layout.html" if not hx_request else "_partial_base.html" %}

{% block title %}ホーム{% endblock %}

{% block main %}
  <!-- ページ固有のコンテンツ -->
{% endblock %}
```

---

## HTMXパーシャル更新パターン

### 動作概要

| リクエスト種別 | HX-Requestヘッダー | サーバーが返すもの | 結果 |
|---|---|---|---|
| ブラウザ直接アクセス | なし | フルページ（`_app_layout.html` 継承） | 初期ロード |
| HTMXナビゲーション | `true` | `<main>` 内のHTMLのみ（`_partial_base.html` 継承） | `#main` のみ差し替え |

### サイドバーのリンク

```html
<a href="/home"
   hx-get="/home"
   hx-target="#main"
   hx-swap="innerHTML"
   hx-push-url="true">
  ホーム
</a>
```

- `hx-target="#main"` → `<main id="main">` の中身を差し替え
- `hx-push-url="true"` → ブラウザのURLを更新（戻るボタンが機能する）
- `href="/home"` → HTMXが無効な場合のフォールバック

### `hx_request` の渡し方

`render()` ヘルパーが自動でセットするため、ルートハンドラ側での記述は不要（後述）。

---

## `render()` ヘルパー

**ファイル**: `app/core/templates.py`

共通コンテキスト（`username`・`hx_request`）を自動付与してテンプレートをレンダリングする。  
`username` は `get_current_user` が `request.state.user` にセット済みのものを参照する。

```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

def render(request: Request, template_name: str, context: dict = {}) -> HTMLResponse:
    base = {
        "request": request,
        "username": getattr(request.state, "user", None),
        "hx_request": request.headers.get("HX-Request") == "true",
    }
    return templates.TemplateResponse(template_name, {**base, **context})
```

### 使い方

```python
from app.core.templates import render

@router.get("/home")
async def home(request: Request):
    return render(request, "home.html", {"active_page": "home"})

@router.get("/chat-ui")
async def chat_ui(request: Request):
    return render(request, "chat_ui.html", {
        "active_page": "chat",
        "thread_id": request.cookies.get("session_token"),
    })
```

ルーターレベルの `Depends(get_current_user)` が先に実行されるため、
ルートハンドラ内で再度 `Depends` を宣言する必要はない。

---

## ページ固有JSパターン

**原則**: カスタムJSは `app/static/js/<画面名>.js` に分離する。

テンプレートへの動的な値の渡し方は、インラインJSではなく **data属性** を使う。

```html
<!-- chat_ui.html の body 内 -->
<div id="chat-app" data-thread-id="{{ thread_id }}"></div>
```

```javascript
// static/js/chat.js
const THREAD_ID = document.getElementById("chat-app").dataset.threadId;
```

### `_base.html` でのscriptsブロック

```html
<head>
  ...
  {% block scripts %}{% endblock %}
</head>
```

各テンプレートでページ固有スクリプトを追加:

```html
{% block scripts %}
<script src="/static/js/chat.js" defer></script>
{% endblock %}
```

---

## エラーページ

**ファイル**: `app/templates/errors/404.html`、`app/templates/errors/500.html`  
両方とも `_base.html` を継承する（サイドバーなし）。

### `main.py` への登録

```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404,
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request},
        status_code=500,
    )
```
