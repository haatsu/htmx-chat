function initChat() {
  const chatApp = document.getElementById("chat-app");
  if (!chatApp || chatApp._initialized) return;
  chatApp._initialized = true;

  const THREAD_ID = chatApp.dataset.threadId;
  const messagesEl = document.getElementById("messages");
  const inputEl = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");

  inputEl.addEventListener("input", () => {
    inputEl.style.height = "auto";
    inputEl.style.height = inputEl.scrollHeight + "px";
  });

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener("click", sendMessage);

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    inputEl.value = "";
    inputEl.style.height = "auto";
    inputEl.disabled = true;
    sendBtn.disabled = true;

    appendUserMessage(text);
    const assistantBubble = appendAssistantSpinner();

    let fullText = "";
    let pendingRender = false;

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
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = JSON.parse(line.slice(6));
          if (payload.done) break;

          fullText += payload.text;

          if (!pendingRender) {
            pendingRender = true;
            requestAnimationFrame(() => {
              assistantBubble.innerHTML = DOMPurify.sanitize(marked.parse(fullText));
              pendingRender = false;
              messagesEl.scrollTop = messagesEl.scrollHeight;
            });
          }
        }
      }

      if (fullText) {
        assistantBubble.innerHTML = DOMPurify.sanitize(marked.parse(fullText));
      } else {
        assistantBubble.textContent = "(応答がありませんでした)";
      }
    } catch (err) {
      assistantBubble.textContent = "エラーが発生しました。";
      console.error(err);
    } finally {
      inputEl.disabled = false;
      sendBtn.disabled = false;
      inputEl.focus();
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }
  }

  function appendUserMessage(text) {
    const wrapper = document.createElement("div");
    wrapper.className = "flex justify-end";
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble chat-bubble-primary max-w-[70%] whitespace-pre-wrap";
    bubble.textContent = text;
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendAssistantSpinner() {
    const wrapper = document.createElement("div");
    wrapper.className = "flex justify-start";
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble max-w-[70%] md-content";
    bubble.innerHTML =
      '<span class="flex items-center gap-2 opacity-60">' +
      '<span class="loading loading-dots loading-sm"></span>' +
      '<span class="text-sm">考え中...</span>' +
      "</span>";
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
  }
}

document.addEventListener("DOMContentLoaded", initChat);
document.addEventListener("htmx:afterSettle", initChat);
