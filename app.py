# ============================================================
#  ChatPy — Flask + Google Gemini API
#  Jalankan:  python app.py
#  Buka:      http://localhost:5000
# ============================================================

from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import os

app = Flask(__name__)

# ── API Key diambil dari environment variable (aman untuk deploy) ──
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "ISI_API_KEY_KAMU_DISINI")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
# ──────────────────────────────────────────────────────────────

HTML_PAGE = """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>ChatPy</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: #111;
      color: #f5c518;
      font-family: 'Segoe UI', sans-serif;
      display: flex;
      flex-direction: column;
      height: 100vh;
    }

    /* ── Header ── */
    header {
      background: #1a1a1a;
      border-bottom: 2px solid #f5c518;
      padding: 14px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-shrink: 0;
    }
    header .logo {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    header .logo span.icon {
      background: #f5c518;
      color: #111;
      font-weight: 900;
      font-size: 1.1rem;
      width: 36px; height: 36px;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    header h1 { font-size: 1.3rem; letter-spacing: 2px; color: #f5c518; }
    header small { color: #aaa; font-size: 0.72rem; display: block; }

    #clearBtn {
      background: transparent;
      border: 1px solid #f5c518;
      color: #f5c518;
      padding: 6px 14px;
      border-radius: 20px;
      cursor: pointer;
      font-size: 0.8rem;
      transition: background .2s;
      flex-shrink: 0;
    }
    #clearBtn:hover { background: #f5c518; color: #111; }

    /* ── Chat area ── */
    #chat {
      flex: 1;
      overflow-y: auto;
      padding: 20px 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .bubble {
      max-width: 80%;
      padding: 12px 16px;
      border-radius: 18px;
      line-height: 1.6;
      font-size: 0.93rem;
      word-break: break-word;
      white-space: pre-wrap;
      animation: fadeIn .25s ease;
    }
    @keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }

    .bubble.user {
      background: #f5c518;
      color: #111;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
    }
    .bubble.ai {
      background: #1e1e1e;
      color: #f0f0f0;
      border: 1px solid #333;
      align-self: flex-start;
      border-bottom-left-radius: 4px;
    }
    .bubble.ai .sender { color: #f5c518; font-weight: 700; margin-bottom: 4px; font-size: 0.8rem; }
    .bubble .time { font-size: 0.68rem; opacity: .5; margin-top: 6px; text-align: right; }

    /* typing dots */
    .typing { display: flex; gap: 5px; padding: 14px 18px; }
    .typing span {
      width: 8px; height: 8px; background: #f5c518;
      border-radius: 50%; animation: bounce .9s infinite;
    }
    .typing span:nth-child(2){animation-delay:.2s}
    .typing span:nth-child(3){animation-delay:.4s}
    @keyframes bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-8px)}}

    /* ── Input bar ── */
    #inputBar {
      background: #1a1a1a;
      border-top: 2px solid #f5c518;
      padding: 12px 14px;
      display: flex;
      gap: 10px;
      align-items: flex-end;
      flex-shrink: 0;
    }
    #userInput {
      flex: 1;
      background: #111;
      border: 1px solid #f5c518;
      color: #f5c518;
      padding: 10px 14px;
      border-radius: 22px;
      font-size: 0.93rem;
      resize: none;
      max-height: 120px;
      outline: none;
      line-height: 1.5;
    }
    #userInput::placeholder { color: #555; }
    #sendBtn {
      background: #f5c518;
      color: #111;
      border: none;
      width: 44px; height: 44px;
      border-radius: 50%;
      font-size: 1.2rem;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: transform .15s, background .2s;
      flex-shrink: 0;
    }
    #sendBtn:hover { transform: scale(1.1); background: #ffd700; }
    #sendBtn:disabled { opacity: .4; cursor: not-allowed; }

    /* scrollbar */
    #chat::-webkit-scrollbar { width: 4px; }
    #chat::-webkit-scrollbar-track { background: #111; }
    #chat::-webkit-scrollbar-thumb { background: #f5c518; border-radius: 4px; }
  </style>
</head>
<body>

<header>
  <div class="logo">
    <span class="icon">C</span>
    <div>
      <h1>ChatPy</h1>
      <small>Powered by Gemini AI</small>
    </div>
  </div>
  <button id="clearBtn" onclick="clearHistory()">🗑 Hapus Chat</button>
</header>

<div id="chat"></div>

<div id="inputBar">
  <textarea id="userInput" rows="1" placeholder="Tulis pesan..."></textarea>
  <button id="sendBtn" onclick="sendMessage()">➤</button>
</div>

<script>
  const chatEl   = document.getElementById('chat');
  const inputEl  = document.getElementById('userInput');
  const sendBtn  = document.getElementById('sendBtn');
  const STORAGE_KEY = 'chatpy_history';

  // ── Load history from localStorage ──────────────────────────
  let history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');

  function saveHistory() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  }

  function now() {
    return new Date().toLocaleTimeString('id-ID', {hour:'2-digit',minute:'2-digit'});
  }

  function addBubble(role, text, time) {
    const wrap = document.createElement('div');
    wrap.className = 'bubble ' + (role === 'user' ? 'user' : 'ai');
    if (role === 'ai') {
      wrap.innerHTML = `<div class="sender">⚡ ChatPy</div>${escHtml(text)}<div class="time">${time}</div>`;
    } else {
      wrap.innerHTML = `${escHtml(text)}<div class="time">${time}</div>`;
    }
    chatEl.appendChild(wrap);
    chatEl.scrollTop = chatEl.scrollHeight;
    return wrap;
  }

  function escHtml(t) {
    return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function showTyping() {
    const d = document.createElement('div');
    d.className = 'bubble ai typing';
    d.id = 'typingDots';
    d.innerHTML = '<span></span><span></span><span></span>';
    chatEl.appendChild(d);
    chatEl.scrollTop = chatEl.scrollHeight;
  }
  function removeTyping() {
    const d = document.getElementById('typingDots');
    if (d) d.remove();
  }

  // ── Render saved history on load ─────────────────────────────
  history.forEach(m => addBubble(m.role, m.text, m.time));

  // ── Send message ─────────────────────────────────────────────
  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    const t = now();
    addBubble('user', text, t);
    history.push({ role: 'user', text, time: t });
    saveHistory();

    inputEl.value = '';
    inputEl.style.height = 'auto';
    sendBtn.disabled = true;
    showTyping();

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: history })
      });
      const data = await res.json();
      removeTyping();

      const reply = data.reply || data.error || 'Tidak ada respons.';
      const rt = now();
      addBubble('ai', reply, rt);
      history.push({ role: 'ai', text: reply, time: rt });
      saveHistory();
    } catch (e) {
      removeTyping();
      addBubble('ai', '⚠️ Gagal menghubungi server. Pastikan Flask berjalan.', now());
    } finally {
      sendBtn.disabled = false;
    }
  }

  function clearHistory() {
    if (!confirm('Hapus semua riwayat chat?')) return;
    history = [];
    saveHistory();
    chatEl.innerHTML = '';
  }

  // Enter kirim, Shift+Enter baris baru
  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  // Auto-resize textarea
  inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = inputEl.scrollHeight + 'px';
  });
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/chat", methods=["POST"])
def chat():
    data    = request.get_json()
    message = data.get("message", "").strip()
    history = data.get("history", [])   # dipakai untuk konteks

    if not message:
        return jsonify({"error": "Pesan kosong."}), 400

    try:
        # Bangun konteks percakapan dari history
        conversation = []
        for h in history[:-1]:          # hilangkan pesan terakhir (sudah ada di message)
            role = "user" if h["role"] == "user" else "model"
            conversation.append({"role": role, "parts": [h["text"]]})

        chat_session = model.start_chat(history=conversation)
        response     = chat_session.send_message(message)
        return jsonify({"reply": response.text})

    except Exception as e:
        return jsonify({"error": f"Gemini error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)