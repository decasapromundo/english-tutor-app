import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import anthropic
except ImportError:
    print("❌ Missing dependency. Run: pip3 install anthropic")
    exit(1)

PORT = int(os.environ.get("PORT", 3001))
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=API_KEY)

SYSTEM_PROMPT = """You are an English tutor specialized in helping Brazilian cruise ship workers improve their English. You use the CEFR framework (A1, A2, B1, B2, C1, C2) to evaluate and guide students.

IMPORTANT RULES:
- Always communicate instructions and explanations in PORTUGUESE (Brazilian).
- Only use English when conducting exercises or role-plays.
- Be warm, encouraging, and practical. Focus on real cruise ship scenarios (guests, colleagues, safety, service).
- Keep responses concise — this is a chat interface, not a lecture.
- Always show the student's current CEFR level at the top of your response using this format: 🎯 Nível atual: [LEVEL]
- If the level is not yet determined, use: 🎯 Nível atual: Em avaliação...

PLACEMENT TEST (trigger when student says "começar" or "iniciar teste"):
Run 10 questions escalating from A1 to C1. Ask ONE question at a time and wait for the answer.

Questions:
1. (A1) "What is your name?" — simple intro
2. (A1) Fill in: "I ___ a crew member." (am/is/are)
3. (A2) "Describe your job on a cruise ship in 1-2 sentences."
4. (A2) "Choose: Can you help me ___ my luggage? (carry / carries / carrying)"
5. (B1) Respond professionally: "A guest says: I'm not happy with my cabin. It's too noisy."
6. (B1) "Describe what you did yesterday using 3 sentences in the past tense."
7. (B2) Reading: 'The cruise line's policy requires all crew to complete a safety drill within 24 hours of boarding. Failure to comply may result in disciplinary action.' — What happens if someone skips the drill?
8. (B2) "Write a short email (3-4 sentences) to your supervisor saying you'll be 10 minutes late."
9. (C1) "Explain the difference between 'I would have helped' and 'I should have helped'."
10. (C1) "A guest complains that dinner was cold and service was slow. Write a professional response."

After all 10 answers: evaluate → assign CEFR level → explain result in Portuguese → generate 7-day study plan.

LEVEL SCORING: 0-2: A1 | 3-4: A2 | 5-6: B1 | 7-8: B2 | 9-10: C1+

7-DAY STUDY PLAN (after test): Show Day 1-7 with Topic, Skill focus, Est. time 15-20 min. Then say: "Para começar, diga 'dia 1'."

DAILY LESSONS (trigger: "dia 1", "dia 2", etc.):
1. 2-min warm-up | 2. Main exercise | 3. 3 key takeaways | 4. Mini mission

END-OF-WEEK RE-EVALUATION (trigger: "reavaliação"):
Run 5 new questions → compare → update CEFR level → celebrate → suggest next week."""

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>English Tutor — Cruzeiros</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--navy:#0a1628;--ocean:#1a3a5c;--blue:#2563eb;--blue-light:#3b82f6;--gold:#f59e0b;--white:#fff;--gray-400:#94a3b8;--radius:12px}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:linear-gradient(135deg,var(--navy) 0%,var(--ocean) 100%);min-height:100vh;color:var(--white)}
.app{display:flex;flex-direction:column;height:100vh}
.app-header{display:flex;align-items:center;gap:10px;padding:14px 24px;background:rgba(255,255,255,.06);border-bottom:1px solid rgba(255,255,255,.1)}
.header-logo{font-size:1.4rem}.header-title{font-weight:600;font-size:1rem;flex:1}
.btn-reset{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:var(--white);padding:6px 14px;border-radius:8px;cursor:pointer;font-size:.85rem}
.btn-reset:hover{background:rgba(255,255,255,.2)}
.app-main{flex:1;overflow:hidden;display:flex;justify-content:center;align-items:center}
/* Welcome */
.welcome{display:flex;align-items:center;justify-content:center;width:100%;padding:24px}
.welcome-card{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:20px;padding:48px 40px;max-width:480px;width:100%;text-align:center}
.welcome-icon{font-size:3rem;margin-bottom:12px}
.welcome-card h1{font-size:2rem;font-weight:700;margin-bottom:4px}
.welcome-subtitle{color:var(--gold);font-size:.95rem;margin-bottom:16px}
.welcome-desc{color:rgba(255,255,255,.75);line-height:1.6;margin-bottom:24px}
.cefr-levels{display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:28px}
.level{padding:4px 14px;border-radius:20px;font-size:.85rem;font-weight:700}
.level.a1a2{background:rgba(239,68,68,.25);color:#fca5a5;border:1px solid rgba(239,68,68,.4)}
.level.b1b2{background:rgba(245,158,11,.25);color:#fcd34d;border:1px solid rgba(245,158,11,.4)}
.level.c1c2{background:rgba(16,185,129,.25);color:#6ee7b7;border:1px solid rgba(16,185,129,.4)}
.arrow{color:var(--gray-400)}
.btn-primary{background:var(--blue);color:var(--white);border:none;padding:14px 36px;border-radius:var(--radius);font-size:1rem;font-weight:600;cursor:pointer;width:100%;margin-bottom:12px}
.btn-primary:hover{background:var(--blue-light)}
.welcome-hint{color:var(--gray-400);font-size:.82rem}
/* Chat */
.chat-container{display:flex;flex-direction:column;width:100%;max-width:760px;height:100%;padding:0 16px 16px}
.chat-messages{flex:1;overflow-y:auto;padding:16px 0;display:flex;flex-direction:column;gap:16px}
.chat-messages::-webkit-scrollbar{width:4px}
.chat-messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,.2);border-radius:4px}
.chat-empty{margin:auto;padding:32px;text-align:center;color:rgba(255,255,255,.5);font-size:1rem}
.message{display:flex;gap:10px;align-items:flex-start}
.message.user{flex-direction:row-reverse}
.message-avatar{font-size:1.4rem;flex-shrink:0;margin-top:4px}
.message-bubble{max-width:75%;padding:12px 16px;border-radius:var(--radius);line-height:1.6;font-size:.95rem;white-space:pre-wrap}
.message.assistant .message-bubble{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.12)}
.message.user .message-bubble{background:var(--blue)}
.typing{display:flex;gap:5px;align-items:center;padding:14px 18px}
.typing span{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,.5);animation:bounce 1.2s infinite ease-in-out}
.typing span:nth-child(2){animation-delay:.2s}.typing span:nth-child(3){animation-delay:.4s}
@keyframes bounce{0%,80%,100%{transform:scale(.7);opacity:.5}40%{transform:scale(1);opacity:1}}
.quick-actions{display:flex;gap:8px;flex-wrap:wrap;padding:8px 0}
.quick-btn{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);color:rgba(255,255,255,.8);padding:6px 12px;border-radius:20px;font-size:.8rem;cursor:pointer}
.quick-btn:hover:not(:disabled){background:rgba(255,255,255,.18);color:var(--white)}
.quick-btn:disabled{opacity:.4;cursor:not-allowed}
.chat-input-row{display:flex;gap:10px}
.chat-input{flex:1;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:var(--radius);padding:12px 16px;color:var(--white);font-size:.95rem;outline:none}
.chat-input::placeholder{color:rgba(255,255,255,.35)}
.chat-input:focus{border-color:var(--blue-light)}
.btn-send{background:var(--blue);border:none;color:var(--white);padding:12px 18px;border-radius:var(--radius);font-size:1.1rem;cursor:pointer}
.btn-send:hover:not(:disabled){background:var(--blue-light)}
.btn-send:disabled{opacity:.4;cursor:not-allowed}
@media(max-width:600px){.welcome-card{padding:32px 24px}.message-bubble{max-width:88%}}
</style>
</head>
<body>
<div class="app">
  <header class="app-header">
    <span class="header-logo">🚢</span>
    <span class="header-title">English Tutor — Cruzeiros</span>
    <button class="btn-reset" onclick="resetSession()">Nova sessão</button>
  </header>
  <main class="app-main" id="main">
    <div class="welcome">
      <div class="welcome-card">
        <div class="welcome-icon">🚢</div>
        <h1>English Tutor</h1>
        <p class="welcome-subtitle">Para trabalhadores de cruzeiro</p>
        <p class="welcome-desc">Aprenda inglês no seu ritmo com um tutor personalizado. Vamos descobrir seu nível e criar um plano de estudos da semana.</p>
        <div class="cefr-levels">
          <span class="level a1a2">A1/A2</span>
          <span class="arrow">→</span>
          <span class="level b1b2">B1/B2</span>
          <span class="arrow">→</span>
          <span class="level c1c2">C1/C2</span>
        </div>
        <button class="btn-primary" onclick="startChat()">Começar agora</button>
        <p class="welcome-hint">Digite <strong>"começar"</strong> para iniciar o teste de nivelamento</p>
      </div>
    </div>
  </main>
</div>

<script>
let messages = [];

function startChat(autoSend) {
  document.getElementById('main').innerHTML = `
    <div class="chat-container" id="chat">
      <div class="chat-messages" id="msgs">
        <div class="chat-empty">👋 Diga <strong>"começar"</strong> para iniciar o teste de nivelamento.</div>
      </div>
      <div class="quick-actions">
        <button class="quick-btn" onclick="send('começar')">🧪 Iniciar teste</button>
        <button class="quick-btn" onclick="send('dia 1')">📅 Dia 1</button>
        <button class="quick-btn" onclick="send('reavaliação')">🔄 Reavaliação</button>
        <button class="quick-btn" onclick="send('o que posso fazer aqui?')">❓ Ajuda</button>
      </div>
      <form class="chat-input-row" onsubmit="handleSubmit(event)">
        <input id="inp" class="chat-input" placeholder="Digite sua mensagem..." autocomplete="off" autofocus>
        <button class="btn-send" type="submit" id="sendBtn">➤</button>
      </form>
    </div>`;
  if (autoSend) send('começar');
}

function resetSession() {
  messages = [];
  location.reload();
}

function handleSubmit(e) {
  e.preventDefault();
  const inp = document.getElementById('inp');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  send(text);
}

function addMessage(role, content) {
  const msgs = document.getElementById('msgs');
  const empty = msgs.querySelector('.chat-empty');
  if (empty) empty.remove();
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.innerHTML = `<div class="message-avatar">${role === 'assistant' ? '🤖' : '👤'}</div>
    <div class="message-bubble" id="msg-${Date.now()}">${content}</div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div.querySelector('.message-bubble');
}

function setLoading(on) {
  const btns = document.querySelectorAll('.quick-btn, #sendBtn');
  btns.forEach(b => b.disabled = on);
  const msgs = document.getElementById('msgs');
  if (on) {
    const d = document.createElement('div');
    d.className = 'message assistant'; d.id = 'typing-indicator';
    d.innerHTML = '<div class="message-avatar">🤖</div><div class="message-bubble typing"><span></span><span></span><span></span></div>';
    msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight;
  } else {
    const t = document.getElementById('typing-indicator');
    if (t) t.remove();
  }
}

async function send(text) {
  const userMsg = {role: 'user', content: text};
  messages.push(userMsg);
  addMessage('user', text);
  setLoading(true);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({messages})
    });
    setLoading(false);
    if (!res.ok) throw new Error('Server error');

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let full = '';
    const bubble = addMessage('assistant', '');

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
          try {
            const d = JSON.parse(line.slice(6));
            full += d.text;
            bubble.textContent = full;
            document.getElementById('msgs').scrollTop = 99999;
          } catch {}
        }
      }
    }
    messages.push({role: 'assistant', content: full});
  } catch(e) {
    setLoading(false);
    addMessage('assistant', '❌ Erro ao conectar com o servidor. Verifique se o servidor está rodando na porta 3001.');
  }
}
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default logs

    def do_GET(self):
        if urlparse(self.path).path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if urlparse(self.path).path != "/api/chat":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        msgs = body.get("messages", [])

        if not API_KEY:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "ANTHROPIC_API_KEY not set. Add it to your .env file."}).encode())
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=msgs,
            ) as stream:
                for text in stream.text_stream:
                    data = json.dumps({"text": text})
                    self.wfile.write(f"data: {data}\n\n".encode())
                    self.wfile.flush()
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except Exception as e:
            err = json.dumps({"text": f"\n\n❌ Erro da API: {str(e)}"})
            self.wfile.write(f"data: {err}\n\n".encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


if __name__ == "__main__":
    if not API_KEY:
        print("⚠️  ANTHROPIC_API_KEY não encontrada.")
        print("   Crie um arquivo .env com: ANTHROPIC_API_KEY=sua_chave_aqui")
        print()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"✅ Servidor rodando em http://0.0.0.0:{PORT}")
    print("   Abra o link acima no navegador para usar o tutor.")
    print("   Pressione Ctrl+C para parar.\n")
    server.serve_forever()
