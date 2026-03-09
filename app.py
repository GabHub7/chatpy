# ============================================================
#  ChatPy — Flask + Gemini 2.0 Flash + Kirim Foto
#  Jalankan:  python app.py
#  Buka:      http://localhost:5000
# ============================================================

from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import os, base64

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "ISI_API_KEY_KAMU_DISINI")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

HTML_PAGE = """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>ChatPy</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#111;color:#f5c518;font-family:'Segoe UI',sans-serif;display:flex;height:100vh;overflow:hidden}

    /* ── Sidebar ── */
    #sidebar{
      width:260px;background:#1a1a1a;border-right:2px solid #f5c518;
      display:flex;flex-direction:column;transition:transform .3s;
      position:relative;flex-shrink:0;
    }
    #sidebar.hidden{transform:translateX(-100%);position:absolute;height:100%;z-index:100}
    .sidebar-header{
      padding:14px 12px;border-bottom:1px solid #333;
      display:flex;align-items:center;justify-content:space-between;flex-shrink:0
    }
    .sidebar-header span{font-weight:700;font-size:0.95rem;letter-spacing:1px}
    #newChatBtn{
      background:#f5c518;color:#111;border:none;padding:6px 12px;
      border-radius:16px;font-size:0.78rem;font-weight:700;cursor:pointer;transition:background .2s
    }
    #newChatBtn:hover{background:#ffd700}
    #sessionList{flex:1;overflow-y:auto;padding:8px}
    .session-item{
      padding:10px 12px;border-radius:10px;cursor:pointer;
      margin-bottom:4px;transition:background .2s;border:1px solid transparent
    }
    .session-item:hover{background:#252525;border-color:#333}
    .session-item.active{background:#252525;border-color:#f5c518}
    .session-title{font-size:0.83rem;color:#f0f0f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:3px}
    .session-date{font-size:0.7rem;color:#666}
    .session-del{float:right;background:none;border:none;color:#555;cursor:pointer;font-size:0.85rem;padding:0 2px;transition:color .2s}
    .session-del:hover{color:#ff4444}
    #sessionList::-webkit-scrollbar{width:3px}
    #sessionList::-webkit-scrollbar-thumb{background:#f5c518;border-radius:3px}

    /* ── Main ── */
    #main{flex:1;display:flex;flex-direction:column;min-width:0;position:relative}
    header{
      background:#1a1a1a;border-bottom:2px solid #f5c518;
      padding:12px 14px;display:flex;align-items:center;gap:10px;flex-shrink:0
    }
    #toggleSidebar{
      background:none;border:1px solid #f5c518;color:#f5c518;
      width:34px;height:34px;border-radius:8px;cursor:pointer;font-size:1rem;
      display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .2s
    }
    #toggleSidebar:hover{background:#f5c518;color:#111}
    .logo{display:flex;align-items:center;gap:8px}
    .logo .icon{
      background:#f5c518;color:#111;font-weight:900;font-size:1rem;
      width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0
    }
    header h1{font-size:1.2rem;letter-spacing:2px}
    header small{color:#aaa;font-size:0.7rem;display:block}

    /* ── Chat ── */
    #chat{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}
    #chat::-webkit-scrollbar{width:4px}
    #chat::-webkit-scrollbar-thumb{background:#f5c518;border-radius:4px}
    .bubble{
      max-width:82%;padding:11px 15px;border-radius:18px;
      line-height:1.6;font-size:0.92rem;word-break:break-word;
      white-space:pre-wrap;animation:fadeIn .25s ease
    }
    @keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
    .bubble.user{background:#f5c518;color:#111;align-self:flex-end;border-bottom-right-radius:4px}
    .bubble.ai{background:#1e1e1e;color:#f0f0f0;border:1px solid #333;align-self:flex-start;border-bottom-left-radius:4px}
    .bubble.ai .sender{color:#f5c518;font-weight:700;margin-bottom:4px;font-size:0.78rem}
    .bubble .time{font-size:0.67rem;opacity:.45;margin-top:5px;text-align:right}
    .bubble img{max-width:100%;border-radius:10px;margin-bottom:6px;display:block}
    .empty-state{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;opacity:.3}
    .empty-state .big{font-size:2.5rem}
    .empty-state p{font-size:0.85rem;text-align:center}
    .typing{display:flex;gap:5px;padding:14px 18px}
    .typing span{width:7px;height:7px;background:#f5c518;border-radius:50%;animation:bounce .9s infinite}
    .typing span:nth-child(2){animation-delay:.2s}
    .typing span:nth-child(3){animation-delay:.4s}
    @keyframes bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-7px)}}

    /* ── Preview gambar ── */
    #imgPreviewBar{
      display:none;background:#1a1a1a;border-top:1px solid #333;
      padding:8px 12px;align-items:center;gap:10px;flex-shrink:0
    }
    #imgPreviewBar.show{display:flex}
    #imgPreview{width:54px;height:54px;object-fit:cover;border-radius:8px;border:2px solid #f5c518}
    #imgPreviewBar span{font-size:0.8rem;color:#aaa;flex:1}
    #removeImg{background:none;border:none;color:#ff4444;font-size:1.2rem;cursor:pointer}

    /* ── Input ── */
    #inputBar{
      background:#1a1a1a;border-top:2px solid #f5c518;
      padding:10px 12px;display:flex;gap:8px;align-items:flex-end;flex-shrink:0
    }
    #photoBtn{
      background:none;border:1px solid #f5c518;color:#f5c518;
      width:42px;height:42px;border-radius:50%;font-size:1.2rem;
      cursor:pointer;display:flex;align-items:center;justify-content:center;
      transition:background .2s;flex-shrink:0
    }
    #photoBtn:hover{background:#f5c518;color:#111}
    #fileInput{display:none}
    #userInput{
      flex:1;background:#111;border:1px solid #f5c518;color:#f5c518;
      padding:10px 13px;border-radius:20px;font-size:0.92rem;
      resize:none;max-height:110px;outline:none;line-height:1.5
    }
    #userInput::placeholder{color:#444}
    #sendBtn{
      background:#f5c518;color:#111;border:none;
      width:42px;height:42px;border-radius:50%;font-size:1.1rem;
      cursor:pointer;display:flex;align-items:center;justify-content:center;
      transition:transform .15s,background .2s;flex-shrink:0
    }
    #sendBtn:hover{transform:scale(1.1);background:#ffd700}
    #sendBtn:disabled{opacity:.4;cursor:not-allowed}

    #sidebar{position:absolute;height:100%;z-index:100;width:240px}
    #sidebar.hidden{transform:translateX(-100%)}
    #overlay{display:none;position:absolute;inset:0;background:rgba(0,0,0,.5);z-index:99}
    #overlay.show{display:block}
  </style>
</head>
<body>

<div id="sidebar">
  <div class="sidebar-header">
    <span>💬 Riwayat</span>
    <button id="newChatBtn" onclick="newChat()">+ Baru</button>
  </div>
  <div id="sessionList"></div>
</div>

<div id="overlay" onclick="toggleSidebar()"></div>

<div id="main">
  <header>
    <button id="toggleSidebar" onclick="toggleSidebar()">☰</button>
    <div class="logo">
      <span class="icon">C</span>
      <div><h1>ChatPy</h1><small>Powered by Gemini 2.0</small></div>
    </div>
  </header>

  <div id="chat">
    <div class="empty-state" id="emptyState">
      <div class="big">⚡</div>
      <p>Mulai percakapan baru<br/>dengan ChatPy!</p>
    </div>
  </div>

  <!-- Preview gambar sebelum kirim -->
  <div id="imgPreviewBar">
    <img id="imgPreview" src="" alt="preview"/>
    <span>Gambar siap dikirim</span>
    <button id="removeImg" onclick="removeImage()" title="Hapus gambar">✕</button>
  </div>

  <div id="inputBar">
    <button id="photoBtn" onclick="document.getElementById('fileInput').click()" title="Kirim foto">📷</button>
    <input type="file" id="fileInput" accept="image/*" onchange="handleImage(event)"/>
    <textarea id="userInput" rows="1" placeholder="Tulis pesan atau kirim foto..."></textarea>
    <button id="sendBtn" onclick="sendMessage()">➤</button>
  </div>
</div>

<script>
  const chatEl  = document.getElementById('chat');
  const inputEl = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  const STORE   = 'chatpy_sessions';
  const ACTIVE  = 'chatpy_active';

  let sessions  = JSON.parse(localStorage.getItem(STORE) || '{}');
  let activeId  = localStorage.getItem(ACTIVE) || null;
  let pendingImg = null; // { base64, mimeType, dataUrl }

  function save() {
    localStorage.setItem(STORE, JSON.stringify(sessions));
    localStorage.setItem(ACTIVE, activeId || '');
  }
  function now() { return new Date().toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'}); }
  function dateStr() { return new Date().toLocaleDateString('id-ID',{day:'2-digit',month:'short',year:'numeric'}); }
  function uid() { return Date.now().toString(36); }
  function esc(t) { return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  // ── Sidebar ──────────────────────────────────────────────
  function renderSidebar() {
    const list = document.getElementById('sessionList');
    const ids  = Object.keys(sessions).sort((a,b)=>b.localeCompare(a));
    if (!ids.length) {
      list.innerHTML='<div style="color:#555;font-size:.8rem;text-align:center;padding:20px">Belum ada riwayat</div>';
      return;
    }
    list.innerHTML = ids.map(id => {
      const s = sessions[id];
      const active = id===activeId?'active':'';
      return `<div class="session-item ${active}" onclick="loadSession('${id}')">
        <button class="session-del" onclick="delSession(event,'${id}')">🗑</button>
        <div class="session-title">${esc(s.title)}</div>
        <div class="session-date">${s.date}</div>
      </div>`;
    }).join('');
  }

  function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('hidden');
    document.getElementById('overlay').classList.toggle('show');
  }

  function newChat() {
    const id = uid();
    sessions[id] = {id, title:'Chat baru', date:dateStr(), messages:[]};
    activeId = id;
    save(); renderSidebar(); renderChat();
  }

  function loadSession(id) {
    activeId = id; save(); renderSidebar(); renderChat();
    if (window.innerWidth<=600) toggleSidebar();
  }

  function delSession(e, id) {
    e.stopPropagation();
    if (!confirm('Hapus percakapan ini?')) return;
    delete sessions[id];
    if (activeId===id) activeId=null;
    save(); renderSidebar(); renderChat();
  }

  // ── Chat render ──────────────────────────────────────────
  function renderChat() {
    chatEl.innerHTML='';
    if (!activeId||!sessions[activeId]||!sessions[activeId].messages.length) {
      chatEl.innerHTML=`<div class="empty-state" id="emptyState">
        <div class="big">⚡</div><p>Mulai percakapan baru<br/>dengan ChatPy!</p></div>`;
      return;
    }
    sessions[activeId].messages.forEach(m => addBubble(m.role, m.text, m.time, m.imageUrl, false));
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  function addBubble(role, text, time, imageUrl, scroll=true) {
    const es = document.getElementById('emptyState');
    if (es) es.remove();
    const w = document.createElement('div');
    w.className = 'bubble '+(role==='user'?'user':'ai');
    let inner = '';
    if (imageUrl) inner += `<img src="${imageUrl}" alt="gambar"/>`;
    if (role==='ai') {
      inner = `<div class="sender">⚡ ChatPy</div>${inner}${esc(text)}<div class="time">${time}</div>`;
    } else {
      inner += `${esc(text)}<div class="time">${time}</div>`;
    }
    w.innerHTML = inner;
    chatEl.appendChild(w);
    if (scroll) chatEl.scrollTop = chatEl.scrollHeight;
  }

  function showTyping() {
    const d=document.createElement('div');
    d.className='bubble ai typing';d.id='typingDots';
    d.innerHTML='<span></span><span></span><span></span>';
    chatEl.appendChild(d);chatEl.scrollTop=chatEl.scrollHeight;
  }
  function removeTyping(){const d=document.getElementById('typingDots');if(d)d.remove();}

  // ── Gambar ───────────────────────────────────────────────
  function handleImage(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      const dataUrl  = ev.target.result;
      const base64   = dataUrl.split(',')[1];
      const mimeType = file.type;
      pendingImg = {base64, mimeType, dataUrl};
      document.getElementById('imgPreview').src = dataUrl;
      document.getElementById('imgPreviewBar').classList.add('show');
    };
    reader.readAsDataURL(file);
    e.target.value='';
  }

  function removeImage() {
    pendingImg=null;
    document.getElementById('imgPreviewBar').classList.remove('show');
    document.getElementById('imgPreview').src='';
  }

  // ── Send ─────────────────────────────────────────────────
  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text && !pendingImg) return;

    if (!activeId||!sessions[activeId]) newChat();

    const t        = now();
    const imageUrl = pendingImg ? pendingImg.dataUrl : null;
    const imgData  = pendingImg ? {base64:pendingImg.base64, mimeType:pendingImg.mimeType} : null;

    addBubble('user', text||'📷 Gambar dikirim', t, imageUrl);
    sessions[activeId].messages.push({role:'user', text:text||'📷 Gambar dikirim', time:t, imageUrl});

    if (sessions[activeId].messages.length===1) {
      sessions[activeId].title = (text||'Gambar').slice(0,30)+(text.length>30?'…':'');
    }
    save(); renderSidebar(); removeImage();

    inputEl.value=''; inputEl.style.height='auto';
    sendBtn.disabled=true; showTyping();

    try {
      const res = await fetch('/chat',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          message: text||'Tolong analisa gambar ini.',
          history: sessions[activeId].messages,
          image: imgData
        })
      });
      const data = await res.json();
      removeTyping();
      const reply = data.reply||data.error||'Tidak ada respons.';
      const rt = now();
      addBubble('ai', reply, rt, null);
      sessions[activeId].messages.push({role:'ai', text:reply, time:rt});
      save();
    } catch(e) {
      removeTyping();
      addBubble('ai','⚠️ Gagal menghubungi server.', now(), null);
    } finally {
      sendBtn.disabled=false;
    }
  }

  // ── Init ─────────────────────────────────────────────────
  // Selalu sembunyikan sidebar saat pertama load di semua ukuran layar
  document.getElementById('sidebar').classList.add('hidden');
  renderSidebar(); renderChat();

  inputEl.addEventListener('keydown', e=>{
    if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();}
  });
  inputEl.addEventListener('input',()=>{
    inputEl.style.height='auto';
    inputEl.style.height=inputEl.scrollHeight+'px';
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
    history = data.get("history", [])
    image   = data.get("image", None)  # {base64, mimeType}

    if not message and not image:
        return jsonify({"error": "Pesan atau gambar kosong."}), 400

    try:
        conversation = []
        for h in history[:-1]:
            role = "user" if h["role"] == "user" else "model"
            conversation.append({"role": role, "parts": [h["text"]]})

        chat_session = model.start_chat(history=conversation)

        # Kalau ada gambar, kirim sebagai multipart
        if image:
            img_bytes = base64.b64decode(image["base64"])
            part_img  = {"mime_type": image["mimeType"], "data": img_bytes}
            response  = chat_session.send_message([part_img, message or "Tolong analisa gambar ini."])
        else:
            response  = chat_session.send_message(message)

        return jsonify({"reply": response.text})

    except Exception as e:
        return jsonify({"error": f"Gemini error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
