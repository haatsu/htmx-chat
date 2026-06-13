# チャットストリーミング仕様

HTMX は Fetch API を使わないため SSE の POST ストリームが扱えない。  
このため、チャット送受信は **素の JS（Fetch API + ReadableStream）** で実装する。

---

## バックエンド：`POST /chat/stream`

**ファイル**: `app/routers/chat.py` に追加

**認証**: `get_current_user` 依存関数で必須

**リクエスト**:
- Content-Type: `application/json`
- Body:
  ```json
  { "message": "ユーザーの入力テキスト", "thread_id": "セッショントークン文字列" }
  ```

**レスポンス**:
- Content-Type: `text/event-stream`
- SSE フォーマット:
  ```
  data: テキストチャンク\n\n
  data: テキストチャンク\n\n
  data: [DONE]\n\n
  ```
  - 各 `data:` はアシスタント応答の差分テキスト（トークン単位）
  - ストリーム終了時に `data: [DONE]` を送信

**実装**:

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import asyncio

from app.core.ai import get_model
from app.core.auth import get_current_user

# チェックポインタはモジュールレベルでシングルトン（会話履歴を保持）
_checkpointer = MemorySaver()

class StreamRequest(BaseModel):
    message: str
    thread_id: str

@router.post("/chat/stream")
async def chat_stream(
    body: StreamRequest,
    model=Depends(get_model),
    username: str = Depends(get_current_user),
):
    agent = create_agent(
        model=model,
        system_prompt="You are a helpful assistant. Answer in the same language as the user.",
        checkpointer=_checkpointer,
    )
    config = {"configurable": {"thread_id": body.thread_id}}

    async def generate():
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=body.message)]},
            config=config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## フロントエンド：JS実装

`app/templates/chat_ui.html` の `<script>` ブロックに記述する。  
テンプレート変数 `{{ thread_id }}` をJSに渡す。

### 初期化

```javascript
const THREAD_ID = "{{ thread_id }}";
const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
```

### テキストエリア自動拡張

```javascript
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = inputEl.scrollHeight + "px";
});
```

### Enter / Shift+Enter ハンドリング

```javascript
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
```

### 送信ボタン

```javascript
sendBtn.addEventListener("click", sendMessage);
```

### メッセージ送信＆ストリーム受信

```javascript
async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  // 入力をリセット・無効化
  inputEl.value = "";
  inputEl.style.height = "auto";
  inputEl.disabled = true;
  sendBtn.disabled = true;

  // ユーザーメッセージをDOMに追加
  appendMessage("user", text);

  // アシスタントの空バブルを追加（ストリームで逐次更新）
  const assistantBubble = appendMessage("assistant", "");

  try {
    const res = await fetch("/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, thread_id: THREAD_ID }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // 未完結行をバッファに残す

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const chunk = line.slice(6); // "data: " を除去
        if (chunk === "[DONE]") break;
        assistantBubble.textContent += chunk;
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }
    }
  } catch (err) {
    assistantBubble.textContent = "エラーが発生しました。";
    console.error(err);
  } finally {
    inputEl.disabled = false;
    sendBtn.disabled = false;
    inputEl.focus();
  }
}
```

### メッセージバブルの追加

```javascript
function appendMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = role === "user"
    ? "flex justify-end mb-2"
    : "flex justify-start mb-2";

  const bubble = document.createElement("div");
  bubble.className = role === "user"
    ? "chat-bubble chat-bubble-primary max-w-[70%] whitespace-pre-wrap"
    : "chat-bubble max-w-[70%] whitespace-pre-wrap";
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  return bubble; // アシスタントバブルは呼び出し元で参照して更新する
}
```

---

## 注意事項

- `MemorySaver` はサーバー再起動で消える（インメモリ）。永続化は今回のスコープ外。
- `thread_id` はセッショントークン（UUID）を流用するため、ユーザーごとに会話履歴が分離される。
- SSEのチャンクに改行文字が含まれる場合、`data:` の値に改行が入るとSSEパースが壊れる。  
  サーバー側で改行を除去するか、base64エンコードするか、JSON文字列でラップすること。  
  **シンプルな対策**: `chunk.replace("\n", "\\n")` でエスケープし、フロント側で `replace(/\\n/g, "\n")` に戻す。
