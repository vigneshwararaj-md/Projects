from flask import Flask, request, jsonify, render_template_string
from agent_core import agent

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#080611">
  <title>Atmos — AI Weather</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root { --bg:#080611; --panel:#100d1b; --muted:#9b96aa; --purple:#9b65ff; --line:rgba(255,255,255,.11); }
    * { box-sizing:border-box; margin:0; padding:0; }
    html { scroll-behavior:smooth; }
    body {
      min-height:100vh; color:#f8f6ff; font-family:'DM Sans',sans-serif;
      background:
        radial-gradient(ellipse at 50% -15%, rgba(105,35,220,.42), transparent 48%),
        radial-gradient(ellipse at 95% 60%, rgba(66,25,140,.19), transparent 35%),
        #080611;
      overflow-x:hidden;
    }
    body:before {
      content:""; position:fixed; inset:0; pointer-events:none; opacity:.13;
      background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);
      background-size:70px 70px; mask-image:linear-gradient(to bottom,black,transparent 85%);
    }
    .orb { position:fixed; width:420px; height:420px; border-radius:50%; filter:blur(110px); opacity:.2; pointer-events:none; z-index:-1; }
    .orb.one { background:#741cff; top:5%; left:-230px; }
    .orb.two { background:#3e42ff; right:-250px; bottom:0; }
    .shell { width:min(1160px, calc(100% - 42px)); margin:auto; }
    
    nav {
      height:54px; width:max-content; max-width:100%; margin:25px auto 0; padding:0 18px;
      display:flex; align-items:center; gap:25px; border:1px solid rgba(255,255,255,.12);
      border-radius:999px; background:rgba(26,23,34,.72); backdrop-filter:blur(18px);
      box-shadow:0 10px 35px rgba(0,0,0,.25);
    }
    .brand { display:flex; align-items:center; gap:8px; font:700 13px Manrope,sans-serif; letter-spacing:.2px; }
    .brand-mark { width:23px; height:23px; display:grid; place-items:center; border-radius:50%; background:linear-gradient(135deg,#c19aff,#7135ed); box-shadow:0 0 18px #8c4cff88; }
    .brand-mark span { font-size:13px; }
    nav a { color:#aaa4b8; text-decoration:none; font-size:11px; transition:.2s; }
    nav a:hover { color:white; }
    .nav-status { color:#c9aaff; font-size:10px; white-space:nowrap; }
    
    .hero { text-align:center; padding:91px 0 38px; position:relative; }
    .eyebrow { display:inline-flex; align-items:center; gap:8px; padding:7px 12px; border:1px solid rgba(179,135,255,.28); border-radius:30px; color:#c9a9ff; background:rgba(117,54,214,.12); font-size:10px; letter-spacing:1.5px; text-transform:uppercase; }
    .pulse { width:6px; height:6px; border-radius:50%; background:#b98cff; box-shadow:0 0 10px #b98cff; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: .4; } 100% { opacity: 1; } }
    h1 { font:500 clamp(48px,8vw,91px)/1.04 Manrope,sans-serif; letter-spacing:-5px; margin:24px 0 15px; }
    h1 .gradient { background:linear-gradient(100deg,#fff 15%,#c6a5ff 55%,#8e58f6 100%); -webkit-background-clip:text; background-clip:text; color:transparent; }
    .hero-copy { color:#a6a0b2; font-size:14px; line-height:1.8; max-width:510px; margin:0 auto; }
    
    .search-card {
      width:min(670px,100%); margin:32px auto 0; padding:9px; display:flex; gap:8px;
      border:1px solid rgba(190,150,255,.3); border-radius:17px; background:rgba(22,17,34,.84);
      box-shadow:0 0 0 5px rgba(135,75,255,.045),0 20px 70px rgba(0,0,0,.35),0 0 55px rgba(116,53,231,.13);
      backdrop-filter:blur(18px); transition: all 0.3s ease;
    }
    .search-card:focus-within { border-color: rgba(190,150,255,.6); box-shadow: 0 0 0 5px rgba(135,75,255,.1), 0 20px 70px rgba(0,0,0,.35), 0 0 55px rgba(116,53,231,.2); }
    .search-icon { align-self:center; padding-left:12px; color:#a987ed; font-size:20px; }
    input { flex:1; min-width:0; border:0; outline:0; color:white; background:transparent; padding:13px 8px; font:14px 'DM Sans',sans-serif; }
    input::placeholder { color:#777184; }
    button { border:0; border-radius:11px; padding:0 23px; color:white; font:600 12px 'DM Sans',sans-serif; cursor:pointer; background:linear-gradient(110deg,#a66cff,#7135e8); box-shadow:0 5px 22px #843ff255; transition:.25s; }
    button:hover { transform:translateY(-2px); box-shadow:0 9px 28px #843ff277; }
    button:disabled { opacity:.65; cursor:wait; transform:none; }
    .hint { margin-top:13px; color:#716b7e; font-size:10px; }
    .hint span { color:#aaa1b9; }
    
    .content { padding:40px 0 90px; }
    .section-head { display:flex; align-items:end; justify-content:space-between; margin-bottom:17px; }
    .section-kicker { color:#9d76e4; font-size:9px; letter-spacing:2px; text-transform:uppercase; margin-bottom:8px; }
    h2 { font:600 20px Manrope,sans-serif; letter-spacing:-.5px; }
    .section-note { color:#716c7d; font-size:10px; }
    
    .result-panel {
      min-height:170px; padding:25px 28px; border:1px solid var(--line); border-radius:18px;
      background:linear-gradient(135deg,rgba(28,22,42,.94),rgba(13,11,21,.94));
      box-shadow:0 18px 55px rgba(0,0,0,.22); position:relative; overflow:hidden;
    }
    .result-panel:after { content:""; position:absolute; width:220px; height:220px; right:-100px; top:-130px; border-radius:50%; background:#8a4dff; filter:blur(85px); opacity:.16; pointer-events:none; }
    .result-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:17px; }
    .result-label { color:#bca0f4; font-size:10px; letter-spacing:1.2px; text-transform:uppercase; }
    .live-dot { color:#8fdaa9; font-size:10px; display:flex; align-items:center; gap:6px; }
    .live-dot::before { content:""; width:6px; height:6px; background:#8fdaa9; border-radius:50%; box-shadow:0 0 8px #8fdaa9; }
    #out { position:relative; z-index:1; color:#d8d3e2; font-size:14px; line-height:1.85; white-space:pre-wrap; overflow-wrap:anywhere; }
    .placeholder { color:#817b8e; }
    .loading { display:flex; align-items:center; gap:12px; color:#b7a6d6; }
    .spinner { width:17px; height:17px; border:2px solid #ffffff30; border-top-color:#bd91ff; border-radius:50%; animation:spin .8s linear infinite; }
    @keyframes spin { to { transform:rotate(360deg); } }
    
    .feature-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:13px; margin-top:15px; }
    .feature { padding:19px; border:1px solid rgba(255,255,255,.08); border-radius:15px; background:rgba(19,16,29,.72); }
    .feature-icon { width:31px; height:31px; display:grid; place-items:center; border-radius:10px; background:rgba(146,91,255,.14); color:#c3a2ff; margin-bottom:13px; font-size:15px; }
    .feature h3 { font:600 12px Manrope,sans-serif; margin-bottom:6px; }
    .feature p { color:#817b8e; font-size:10px; line-height:1.6; }
    
    footer { border-top:1px solid rgba(255,255,255,.07); padding:20px 0 28px; color:#625d6d; font-size:10px; text-align:center; }
    footer b { color:#a98ae0; font-weight:500; }
    
    @media(max-width:650px) {
      h1 { letter-spacing: -2px; }
      .search-card { flex-direction: column; padding: 12px; }
      .search-icon { display: none; }
      button { padding: 14px; width: 100%; }
      .feature-grid { grid-template-columns: 1fr; }
      .section-head { flex-direction: column; align-items: flex-start; gap: 5px; }
    }
  </style>
</head>
<body>
  <div class="orb one"></div>
  <div class="orb two"></div>

  <nav>
    <div class="brand">
      <div class="brand-mark"><span>✦</span></div>
      Atmos
    </div>
    <a href="#">API</a>
    <a href="#">Docs</a>
    <a href="#">Pricing</a>
    <div class="nav-status">● System Operational</div>
  </nav>

  <div class="shell">
    <div class="hero">
      <div class="eyebrow"><div class="pulse"></div> AI-Powered Meteorology</div>
      <h1>Weather,<br><span class="gradient">intelligently.</span></h1>
      <p class="hero-copy">Query real-time global weather conditions using natural language. Our AI extracts your intent, calls the data, and formats it instantly.</p>
      
      <div class="search-card">
        <div class="search-icon">⌕</div>
        <input type="text" id="q" placeholder="e.g., What is the weather in Chennai, India?" autocomplete="off">
        <button onclick="ask()" id="btn">Query</button>
      </div>
      <div class="hint">Press <span>Enter</span> to search. Try "Tokyo" or "London, UK".</div>
    </div>

    <div class="content">
      <div class="section-head">
        <div>
          <div class="section-kicker">Live Output</div>
          <h2>Current Conditions</h2>
        </div>
        <div class="section-note">Powered by OpenWeather & Groq</div>
      </div>

      <div class="result-panel">
        <div class="result-top">
          <div class="result-label">Agent Response</div>
          <div class="live-dot">Live</div>
        </div>
        <div id="out" class="placeholder">Awaiting your query...</div>
      </div>

      <div class="feature-grid">
        <div class="feature">
          <div class="feature-icon">⚡</div>
          <h3>Real-Time Data</h3>
          <p>Direct API integration ensures you get the most up-to-date temperatures and humidity.</p>
        </div>
        <div class="feature">
          <div class="feature-icon">🧠</div>
          <h3>LLM Reasoning</h3>
          <p>Powered by Llama 3. The AI understands natural language and extracts the exact city.</p>
        </div>
        <div class="feature">
          <div class="feature-icon">🌍</div>
          <h3>Global Coverage</h3>
          <p>Query any city, anywhere in the world. The AI automatically resolves country codes.</p>
        </div>
      </div>
    </div>
  </div>

  <footer>
    Built with <b>Python, Flask, LangChain & Groq</b>. &copy; 2026 Atmos.
  </footer>

  <script>
    async function ask() {
      const q = document.getElementById('q').value;
      const out = document.getElementById('out');
      const btn = document.getElementById('btn');
      
      if (!q.trim()) return;

      // Set Loading State
      btn.disabled = true;
      btn.innerText = "...";
      out.className = "";
      out.innerHTML = '<div class="loading"><div class="spinner"></div><span>Analyzing atmospheric data...</span></div>';

      try {
        const r = await fetch('/ask', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({query: q})
        });
        const d = await r.json();
        
        // Display Result
        out.innerText = d.answer;
      } catch (error) {
        out.innerText = "Connection error. Is the server running?";
      } finally {
        // Reset Button
        btn.disabled = false;
        btn.innerText = "Query";
      }
    }

    // Allow pressing "Enter" to search
    document.getElementById('q').addEventListener('keypress', function (e) {
      if (e.key === 'Enter') ask();
    });
  </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('query', '').strip()
    if not user_input:
        return jsonify({'answer': 'Input cannot be empty'})
    try:
        result = agent.invoke({"messages": [("user", user_input)]})
        answer_text = result["messages"][-1].content
        return jsonify({'answer': answer_text})
    except Exception as e:
        return jsonify({'answer': f'Processing failed: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)