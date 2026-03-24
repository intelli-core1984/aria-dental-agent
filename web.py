"""
ARIA — Web interface (browser preview / testing)
Flask server that serves the chat UI and proxies to the Claude agent.
"""
from flask import Flask, request, jsonify, render_template_string
from paths import get_config_path
from dotenv import load_dotenv
import os

load_dotenv(get_config_path())

app = Flask(__name__)

# Lazy-load the agent so missing API key gives a clean error
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        from agent import Agent
        _agent = Agent()
    return _agent


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ARIA — Dental Assistant</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: #080d12;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      font-family: 'Courier New', Courier, monospace;
    }

    .card {
      width: 380px;
      height: 580px;
      background: #0f1419;
      border: 1px solid #1e2d3d;
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 24px 64px rgba(0,0,0,0.6);
    }

    /* Title bar */
    .titlebar {
      background: #161d26;
      padding: 0 14px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
      border-bottom: 1px solid #1e2d3d;
    }
    .titlebar-name {
      color: #00e5a0;
      font-size: 11px;
      font-weight: bold;
      letter-spacing: 0.08em;
    }
    .titlebar-status {
      font-size: 9px;
      color: #3a5a6a;
      letter-spacing: 0.06em;
    }
    .dot {
      display: inline-block;
      width: 7px; height: 7px;
      background: #00e5a0;
      border-radius: 50%;
      margin-right: 6px;
      animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }

    /* Messages */
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 12px 0;
      scroll-behavior: smooth;
    }
    .messages::-webkit-scrollbar { width: 4px; }
    .messages::-webkit-scrollbar-track { background: transparent; }
    .messages::-webkit-scrollbar-thumb { background: #1e2d3d; border-radius: 2px; }

    .msg-block { padding: 6px 14px; }
    .msg-sender {
      font-size: 9px;
      font-weight: bold;
      letter-spacing: 0.08em;
      margin-bottom: 4px;
    }
    .msg-sender.aria  { color: #00e5a0; }
    .msg-sender.user  { color: #5a7a8a; }

    .bubble {
      font-size: 11px;
      line-height: 1.6;
      color: #e8edf2;
      background: #161d26;
      border-radius: 6px;
      padding: 8px 12px;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .bubble.user-bubble {
      background: transparent;
      color: #8aa8b8;
    }
    .bubble.thinking {
      color: #3a5a6a;
      font-style: italic;
    }

    /* Input bar */
    .inputbar {
      background: #161d26;
      border-top: 1px solid #1e2d3d;
      padding: 10px;
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }
    .inputbar input {
      flex: 1;
      background: #1d2733;
      border: 1px solid #263545;
      border-radius: 5px;
      color: #e8edf2;
      font-family: inherit;
      font-size: 11px;
      padding: 8px 12px;
      outline: none;
      transition: border-color 0.15s;
    }
    .inputbar input::placeholder { color: #3a5a6a; }
    .inputbar input:focus { border-color: #00e5a0; }

    .inputbar button {
      background: #00e5a0;
      border: none;
      border-radius: 5px;
      color: #000;
      font-size: 16px;
      font-weight: bold;
      width: 36px;
      cursor: pointer;
      transition: background 0.15s;
      flex-shrink: 0;
    }
    .inputbar button:hover { background: #00ffb3; }
    .inputbar button:disabled { background: #1e2d3d; color: #3a5a6a; cursor: not-allowed; }

    /* No-key warning */
    .warn {
      font-size: 10px;
      color: #e05050;
      text-align: center;
      padding: 6px 14px;
      background: #1a0a0a;
      border-top: 1px solid #3a1010;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="titlebar">
      <span class="titlebar-name">⬡ &nbsp;ARIA &nbsp;·&nbsp; Image Dental</span>
      <span class="titlebar-status"><span class="dot"></span>ONLINE</span>
    </div>

    <div class="messages" id="messages"></div>

    {% if not license_key %}
    <div class="warn">⚠ No license key — add ARIA_LICENSE_KEY to ~/Library/Application Support/ARIA/.env</div>
    {% endif %}

    <div class="inputbar">
      <input id="inp" type="text" placeholder="Ask a question..." autocomplete="off" {% if not license_key %}disabled{% endif %} />
      <button id="send" {% if not license_key %}disabled{% endif %}>→</button>
    </div>
  </div>

  <script>
    const msgs = document.getElementById('messages');
    const inp  = document.getElementById('inp');
    const btn  = document.getElementById('send');

    function addMsg(sender, text, cls) {
      const block = document.createElement('div');
      block.className = 'msg-block';
      block.innerHTML = `
        <div class="msg-sender ${cls}">${sender}</div>
        <div class="bubble ${cls === 'user' ? 'user-bubble' : ''} ${text === 'thinking...' ? 'thinking' : ''}" id="b-${Date.now()}">${text}</div>
      `;
      msgs.appendChild(block);
      msgs.scrollTop = msgs.scrollHeight;
      return block.querySelector('.bubble');
    }

    async function send() {
      const q = inp.value.trim();
      if (!q) return;
      inp.value = '';
      btn.disabled = true;
      inp.disabled = true;

      addMsg('YOU', q, 'user');
      const thinking = addMsg('ARIA', 'thinking...', 'aria');

      try {
        const res  = await fetch('/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q })
        });
        const data = await res.json();
        thinking.textContent = data.answer || data.error || 'No response.';
        thinking.classList.remove('thinking');
      } catch(e) {
        thinking.textContent = 'Connection error.';
        thinking.classList.remove('thinking');
      }

      btn.disabled = false;
      inp.disabled = false;
      inp.focus();
    }

    btn.addEventListener('click', send);
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });

    // Welcome message
    addMsg('ARIA', 'Hi. Ask me anything about the schedule, production, or patients.', 'aria');
    inp.focus();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    license_key = bool(os.getenv("ARIA_LICENSE_KEY", "").startswith("aria_"))
    return render_template_string(HTML, license_key=license_key)


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = (data or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400
    try:
        answer = get_agent().ask(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(port=port, debug=False)
