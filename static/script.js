const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const send = document.getElementById("send");
const chips = document.getElementById("chips");
const history = [];

function addMessage(text, who, extra = "") {
  const el = document.createElement("div");
  el.className = `msg ${who} ${extra}`.trim();
  el.textContent = text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

async function ask(text) {
  chips.hidden = true;
  addMessage(text, "user");
  history.push({ role: "user", content: text });
  const typing = addMessage("Thinking…", "bot", "typing");
  send.disabled = true;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history }),
    });
    const data = await res.json();
    typing.remove();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    history.push({ role: "assistant", content: data.reply });
    addMessage(data.reply, "bot");
  } catch (err) {
    typing.remove();
    addMessage(err.message, "bot", "error");
    history.pop();
  } finally {
    send.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  ask(text);
});

(async function init() {
  try {
    const p = await (await fetch("/api/profile")).json();
    document.getElementById("botName").textContent = p.assistant_name;
    document.getElementById("botSub").textContent = `Ask me anything about ${p.name}`;
    document.title = `${p.assistant_name} · ${p.name}`;
    addMessage(`Hi, I'm ${p.assistant_name}, ${p.name}'s portfolio assistant. What would you like to know?`, "bot");
    (p.suggested_questions || []).forEach((q) => {
      const b = document.createElement("button");
      b.type = "button"; b.textContent = q;
      b.addEventListener("click", () => ask(q));
      chips.appendChild(b);
    });
  } catch {
    addMessage("Can't reach the server. Start it with: python app.py", "bot", "error");
  }
})();
