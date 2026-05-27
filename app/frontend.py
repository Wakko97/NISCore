from fastapi.responses import HTMLResponse


def admin_html() -> HTMLResponse:
    return HTMLResponse("""
<!doctype html>
<html lang='de'>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width,initial-scale=1'/>
<title>NISCore Admin</title>
<style>
body{font-family:Inter,Arial;background:#0b1020;color:#e8ecff;margin:0} .wrap{max-width:1100px;margin:20px auto;padding:0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}.card{background:#121a33;border:1px solid #2a3768;border-radius:12px;padding:14px}
input,textarea,button{width:100%;padding:8px;margin-top:6px;border-radius:8px;border:1px solid #334477;background:#0e1630;color:#fff}
button{background:#3659d9;cursor:pointer} pre{white-space:pre-wrap;background:#0e1630;padding:8px;border-radius:8px;min-height:80px}
</style></head><body><div class='wrap'><h1>NISCore Admin Dashboard</h1>
<div class='grid'>
<div class='card'><h3>Client registrieren</h3><input id='asset' placeholder='asset_id'><input id='serial' placeholder='serial'><input id='dtype' placeholder='device_type'><button onclick='registerClient()'>Anlegen</button><pre id='out1'></pre></div>
<div class='card'><h3>Diagnose hochladen</h3><input id='d_asset' placeholder='asset_id'><input id='tech' placeholder='technician'><input id='result' placeholder='result z.B. smart_critical'><textarea id='raw' placeholder='raw_json'></textarea><button onclick='diagnostic()'>Senden</button><pre id='out2'></pre></div>
<div class='card'><h3>Wipe Job</h3><input id='w_asset' placeholder='asset_id'><input id='method' placeholder='method'><input id='std' placeholder='standard'><button onclick='wipe()'>Starten</button><pre id='out3'></pre></div>
<div class='card'><h3>ISO Build</h3><input id='profile' placeholder='profile' value='workshop'><button onclick='iso()'>ISO erzeugen</button><pre id='out4'></pre></div>
<div class='card'><h3>Migration Job</h3><input id='tenant' placeholder='tenant' value='default'><input id='jtype' placeholder='job_type' value='imap'><input id='src' placeholder='source'><input id='dst' placeholder='target'><button onclick='migration()'>Erstellen</button><pre id='out5'></pre></div>
<div class='card'><h3>Health</h3><button onclick='health()'>Prüfen</button><pre id='out6'></pre></div>
<div class='card'><h3>Live Status Stream</h3><input id='liveToken' placeholder='NISCORE_LIVE_TOKEN'><button onclick='connectLive()'>Verbinden</button><pre id='out7'></pre></div>
</div></div>
<script>
async function post(url, body, out){ const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); document.getElementById(out).textContent=await r.text(); }
async function health(){ const r=await fetch('/health'); document.getElementById('out6').textContent=await r.text(); }
function registerClient(){ post('/api/v1/clients/register',{tenant_id:'default',asset_id:asset.value,serial_number:serial.value,device_type:dtype.value},'out1'); }
function diagnostic(){ post('/api/v1/diagnostics/results',{asset_id:d_asset.value,technician:tech.value,result:result.value,raw_json:raw.value||'{}'},'out2'); }
function wipe(){ post('/api/v1/wipe/jobs',{asset_id:w_asset.value,method:method.value,standard:std.value},'out3'); }
function iso(){ post('/api/v1/workshop/iso/build',{profile:profile.value,base_distribution:'debian-trixie',include_tools:['smartmontools','nvme-cli']},'out4'); }
function migration(){ post('/api/v1/migrations/jobs',{tenant_id:tenant.value,job_type:jtype.value,source:src.value,target:dst.value},'out5'); }

let liveSocket;
function connectLive(){
  if(liveSocket){ liveSocket.close(); }
  const token = document.getElementById('liveToken').value;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  liveSocket = new WebSocket(`${proto}://${location.host}/ws/live/status?token=${encodeURIComponent(token)}`);
  liveSocket.onopen = () => { document.getElementById('out7').textContent = 'Live-Verbindung aktiv'; };
  liveSocket.onmessage = (evt) => {
    const prev = document.getElementById('out7').textContent;
    document.getElementById('out7').textContent = `${evt.data}
${prev}`.trim();
  };
  liveSocket.onclose = () => { document.getElementById('out7').textContent = 'Live-Verbindung beendet'; };
}

</script></body></html>
:root{--bg:#0b1020;--panel:#121a33;--panel2:#0e1630;--line:#2a3768;--line2:#334477;--text:#e8ecff;--muted:#9aa6d1;--accent:#6f9bff;--ok:#1fcf9c;--err:#ff6b6b}
*{box-sizing:border-box}body{margin:0;font-family:Inter,Arial,sans-serif;background:var(--bg);color:var(--text)}
.layout{display:grid;grid-template-columns:280px 1fr;min-height:100vh}.sidebar{border-right:1px solid var(--line);padding:20px;background:#0d1430}
.brand{font-size:20px;font-weight:700}.muted{color:var(--muted);font-size:13px}.nav a{display:block;padding:10px;border:1px solid transparent;border-radius:10px;color:var(--text);text-decoration:none;margin-top:6px}
.nav a:hover{border-color:var(--line2);background:var(--panel)}
.main{padding:20px}.top{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.badge{padding:6px 10px;border-radius:999px;background:#143353;color:#b9d6ff;font-size:12px;border:1px solid #2f5c8f}
.token{display:flex;gap:8px;align-items:center}.token input{width:260px}
.grid{margin-top:18px;display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px}
.card h3{margin:0 0 10px 0}
label{display:block;font-size:12px;color:var(--muted);margin-top:8px}
input,textarea,button{width:100%;padding:9px;margin-top:4px;border-radius:10px;border:1px solid var(--line2);background:var(--panel2);color:#fff}
textarea{min-height:78px;resize:vertical}
button{background:#3558d8;cursor:pointer;font-weight:600}
button:hover{filter:brightness(1.08)}
pre{white-space:pre-wrap;background:var(--panel2);padding:10px;border-radius:10px;border:1px solid #25355f;min-height:70px;max-height:260px;overflow:auto}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.small{font-size:12px;color:var(--muted)}
@media(max-width:960px){.layout{grid-template-columns:1fr}.sidebar{border-right:none;border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<div class='layout'>
  <aside class='sidebar'>
    <div class='brand'>NISCore Admin</div>
    <p class='muted'>Control Plane Oberfläche für API-Flows</p>
    <nav class='nav'>
      <a href='#ops'>Operations</a>
      <a href='#migration'>Migration</a>
      <a href='#monitoring'>Monitoring</a>
      <a href='/docs' target='_blank'>Swagger öffnen</a>
    </nav>
  </aside>

  <main class='main'>
    <div class='top'>
      <div>
        <h1 style='margin:0'>Dashboard</h1>
        <div class='small'>Schnellaktionen + Live-Antworten aus der API</div>
      </div>
      <div class='token'>
        <span class='badge'>X-API-Token</span>
        <input id='apiToken' placeholder='optional, wenn NISCORE_API_TOKEN aktiv ist'/>
      </div>
    </div>

    <section class='grid' id='ops'>
      <article class='card'><h3>Health / Ready</h3>
        <div class='row'>
          <button onclick='health()'>GET /health</button>
          <button onclick='ready()'>GET /ready</button>
        </div>
        <pre id='outHealth'></pre>
      </article>

      <article class='card'><h3>Client registrieren</h3>
        <label>asset_id<input id='asset' placeholder='asset-001'></label>
        <label>serial<input id='serial' placeholder='SN-001'></label>
        <label>device_type<input id='dtype' placeholder='laptop'></label>
        <button onclick='registerClient()'>Anlegen</button>
        <pre id='outClient'></pre>
      </article>

      <article class='card'><h3>Diagnose hochladen</h3>
        <label>asset_id<input id='d_asset' placeholder='asset-001'></label>
        <label>technician<input id='tech' placeholder='alice'></label>
        <label>result<input id='result' placeholder='smart_critical'></label>
        <label>raw_json<textarea id='raw' placeholder='{"temp": 70}'></textarea></label>
        <button onclick='diagnostic()'>Senden</button>
        <pre id='outDiag'></pre>
      </article>

      <article class='card'><h3>Wipe Job</h3>
        <label>asset_id<input id='w_asset' placeholder='asset-001'></label>
        <label>method<input id='method' placeholder='nvme-format'></label>
        <label>standard<input id='std' placeholder='nist-800-88'></label>
        <button onclick='wipe()'>Starten</button>
        <pre id='outWipe'></pre>
      </article>
    </section>

    <section class='grid' id='migration'>
      <article class='card'><h3>Migration Job</h3>
        <label>tenant<input id='tenant' value='default'></label>
        <label>job_type<input id='jtype' value='imap'></label>
        <label>source<input id='src' placeholder='imap://old'></label>
        <label>target<input id='dst' placeholder='m365://new'></label>
        <button onclick='migration()'>Erstellen</button>
        <pre id='outMigration'></pre>
      </article>

      <article class='card'><h3>ISO Build</h3>
        <label>profile<input id='profile' value='workshop'></label>
        <button onclick='iso()'>ISO erzeugen</button>
        <pre id='outIso'></pre>
      </article>
    </section>

    <section class='grid' id='monitoring'>
      <article class='card'><h3>Listen laden</h3>
        <div class='row'>
          <button onclick='fetchList("/api/v1/clients?limit=20","outList")'>Clients</button>
          <button onclick='fetchList("/api/v1/recommendations?limit=20","outList")'>Recommendations</button>
        </div>
        <button onclick='fetchList("/api/v1/migrations/jobs?limit=20","outList")' style='margin-top:8px'>Migration Jobs</button>
        <pre id='outList'></pre>
      </article>
    </section>
  </main>
</div>
<script>
function headers(){ const h={"Content-Type":"application/json"}; const t=document.getElementById('apiToken').value.trim(); if(t){h['X-API-Token']=t;} return h; }
async function render(resId, promise){ const el=document.getElementById(resId); try{const r=await promise; const body=await r.text(); el.textContent=`${r.status} ${r.statusText}\n${body}`;}catch(e){el.textContent='Request error: '+e;} }
function post(url, body, out){ return render(out, fetch(url,{method:'POST',headers:headers(),body:JSON.stringify(body)})); }
function patch(url, body, out){ return render(out, fetch(url,{method:'PATCH',headers:headers(),body:JSON.stringify(body)})); }
function fetchList(url, out){ return render(out, fetch(url)); }
function health(){ return render('outHealth', fetch('/health')); }
function ready(){ return render('outHealth', fetch('/ready')); }
function registerClient(){ return post('/api/v1/clients/register',{tenant_id:'default',asset_id:asset.value,serial_number:serial.value,device_type:dtype.value},'outClient'); }
function diagnostic(){ return post('/api/v1/diagnostics/results',{asset_id:d_asset.value,technician:tech.value,result:result.value,raw_json:raw.value||'{}'},'outDiag'); }
function wipe(){ return post('/api/v1/wipe/jobs',{asset_id:w_asset.value,method:method.value,standard:std.value},'outWipe'); }
function iso(){ return post('/api/v1/workshop/iso/build',{profile:profile.value,base_distribution:'debian-trixie',include_tools:['smartmontools','nvme-cli']},'outIso'); }
function migration(){ return post('/api/v1/migrations/jobs',{tenant_id:tenant.value,job_type:jtype.value,source:src.value,target:dst.value},'outMigration'); }
</script>
</body></html>
""")
