from fastapi.responses import HTMLResponse


def admin_html() -> HTMLResponse:
    return HTMLResponse("""
<!doctype html>
<html lang='de'>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width,initial-scale=1'/>
<title>NISCore Operations Console</title>
<style>
:root{--bg:#070b17;--panel:#101a33;--panel2:#0d152c;--line:#243666;--text:#ecf0ff;--muted:#9aabd8;--accent:#7aa2ff;--ok:#22c39a;--warn:#ffcf57;--err:#ff6b7d}
*{box-sizing:border-box} body{margin:0;font-family:Inter,Arial,sans-serif;background:linear-gradient(165deg,#070b17,#0f1a38 65%);color:var(--text)}
.layout{display:grid;grid-template-columns:280px 1fr;min-height:100vh}
.sidebar{padding:22px;border-right:1px solid var(--line);background:rgba(4,9,22,.7)}
.brand{font-size:20px;font-weight:700}.hint{font-size:12px;color:var(--muted)}
.nav a{display:block;margin-top:8px;padding:10px 12px;border-radius:10px;color:var(--text);text-decoration:none;border:1px solid transparent}
.nav a:hover{border-color:var(--line);background:var(--panel)}
.main{padding:20px}.top{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}
.token{display:flex;gap:8px;align-items:center}.token input{min-width:280px}
.pill{font-size:12px;padding:6px 10px;border-radius:999px;border:1px solid #35599c;background:#1a2d58;color:#b8d4ff}
.grid{display:grid;gap:12px;margin-top:14px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{background:rgba(16,26,51,.9);border:1px solid var(--line);padding:14px;border-radius:14px}
.card h3{margin:0 0 8px 0;font-size:16px}
label{display:block;font-size:12px;color:var(--muted);margin-top:7px}
input,textarea,select,button{margin-top:4px;width:100%;padding:9px;border-radius:9px;border:1px solid #2f4479;background:var(--panel2);color:white}
textarea{min-height:88px;resize:vertical}
button{background:#3257d8;cursor:pointer;font-weight:600} button:hover{filter:brightness(1.07)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}
pre{white-space:pre-wrap;background:#0a1227;border:1px solid #283a68;border-radius:10px;padding:10px;max-height:220px;overflow:auto;min-height:68px}
.status{font-size:12px;margin-top:8px}.ok{color:var(--ok)}.warn{color:var(--warn)}.err{color:var(--err)}
@media(max-width:980px){.layout{grid-template-columns:1fr}.sidebar{border-right:none;border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<div class='layout'>
  <aside class='sidebar'>
    <div class='brand'>NISCore Console</div>
    <p class='hint'>Redesigned Unified Operations Console</p>
    <nav class='nav'>
      <a href='#ops'>Operations</a>
      <a href='#security'>Security</a>
      <a href='#migration'>Migration</a>
      <a href='#integrations'>Integrationen</a>
      <a href='/docs' target='_blank'>Swagger öffnen</a>
    </nav>
  </aside>
  <main class='main'>
    <div class='top'>
      <div><h1 style='margin:0'>Operations Dashboard</h1><div class='hint'>Schnellaktionen, Monitoring und Integrationen in einem UI-Flow.</div></div>
      <div class='token'><span class='pill'>Bearer Token</span><input id='apiToken' placeholder='JWT aus /api/v1/auth/login'></div>
    </div>

    <section class='grid' id='ops'>
      <article class='card'><h3>Systemstatus</h3><div class='row'><button onclick='getReq("/health","outSystem")'>GET /health</button><button onclick='getReq("/ready","outSystem")'>GET /ready</button></div><pre id='outSystem'></pre></article>
      <article class='card'><h3>Client registrieren</h3><label>Asset ID<input id='asset' value='asset-001'></label><label>Serial<input id='serial' value='SN-001'></label><label>Typ<input id='dtype' value='laptop'></label><button onclick='registerClient()'>Anlegen</button><pre id='outClient'></pre></article>
      <article class='card'><h3>Diagnose + Empfehlung</h3><label>Asset ID<input id='d_asset' value='asset-001'></label><label>Techniker<input id='tech' value='alice'></label><label>Result<select id='result'><option>smart_critical</option><option>malware_indicator</option><option>backup_missing</option></select></label><label>Raw JSON<textarea id='raw'>{"temp":72,"health":"critical"}</textarea></label><button onclick='diagnostic()'>Senden</button><pre id='outDiag'></pre></article>
    </section>

    <section class='grid' id='security'>
      <article class='card'><h3>Security Check</h3><label>Asset ID<input id='sec_asset' value='asset-001'></label><label>Scan Type<input id='sec_type' value='malware_indicator'></label><label>Details<textarea id='sec_details'>suspicious process detected</textarea></label><button onclick='endpointCheck()'>Prüfen</button><pre id='outSecurity'></pre></article>
      <article class='card'><h3>SSL Monitoring</h3><label>Host<input id='ssl_host' value='example.com'></label><label>Port<input id='ssl_port' value='443'></label><button onclick='sslCheck()'>Check</button><pre id='outSsl'></pre></article>
      <article class='card'><h3>Wipe Job</h3><label>Asset ID<input id='w_asset' value='asset-001'></label><label>Method<input id='method' value='nvme-format'></label><label>Standard<input id='std' value='nist-800-88'></label><button onclick='wipe()'>Starten</button><pre id='outWipe'></pre></article>
    </section>

    <section class='grid' id='migration'>
      <article class='card'><h3>Migration Job</h3><label>Tenant<input id='tenant' value='default'></label><label>Job Type<input id='jtype' value='imap'></label><label>Source<input id='src' value='imap://legacy'></label><label>Target<input id='dst' value='m365://tenant'></label><button onclick='migration()'>Erstellen</button><pre id='outMigration'></pre></article>
      <article class='card'><h3>ISO Build</h3><label>Profil<input id='profile' value='workshop'></label><button onclick='iso()'>Build starten</button><pre id='outIso'></pre></article>
      <article class='card'><h3>Listen</h3><div class='row'><button onclick='getReq("/api/v1/clients?limit=20","outList")'>Clients</button><button onclick='getReq("/api/v1/recommendations?limit=20","outList")'>Recommendations</button></div><button style='margin-top:8px' onclick='getReq("/api/v1/migrations/jobs?limit=20","outList")'>Migration Jobs</button><pre id='outList'></pre></article>
    </section>

    <section class='grid' id='integrations'>
      <article class='card'><h3>NDesk Assets</h3><button onclick='getReq("/api/v1/integrations/ndesk/assets?limit=20","outNdesk")'>Laden</button><pre id='outNdesk'></pre></article>
      <article class='card'><h3>Queue Job Status</h3><label>Job ID<input id='job_id' placeholder='queue job id'></label><button onclick='jobStatus()'>Abfragen</button><pre id='outJob'></pre></article>
    </section>
  </main>
</div>
<script>
function authHeaders(){ const h={"Content-Type":"application/json"}; const t=document.getElementById('apiToken').value.trim(); if(t){h['Authorization']='Bearer '+t;} return h; }
async function render(out, req){ const el=document.getElementById(out); try{ const r=await req; const text=await r.text(); el.textContent=`${r.status} ${r.statusText}\n${text}`; }catch(e){ el.textContent='Request error: '+e; } }
function getReq(url,out){ return render(out, fetch(url,{headers:authHeaders()})); }
function postReq(url,body,out){ return render(out, fetch(url,{method:'POST',headers:authHeaders(),body:JSON.stringify(body)})); }
function registerClient(){ return postReq('/api/v1/clients/register',{tenant_id:'default',asset_id:asset.value,serial_number:serial.value,device_type:dtype.value},'outClient'); }
function diagnostic(){ return postReq('/api/v1/diagnostics/results',{asset_id:d_asset.value,technician:tech.value,result:result.value,raw_json:raw.value||'{}'},'outDiag'); }
function wipe(){ return postReq('/api/v1/wipe/jobs',{asset_id:w_asset.value,method:method.value,standard:std.value},'outWipe'); }
function endpointCheck(){ return postReq('/api/v1/security/endpoint-check',{asset_id:sec_asset.value,scan_type:sec_type.value,details:sec_details.value},'outSecurity'); }
function sslCheck(){ return postReq('/api/v1/web/scans/ssl-check',{host:ssl_host.value,port:parseInt(ssl_port.value||'443',10)},'outSsl'); }
function migration(){ return postReq('/api/v1/migrations/jobs',{tenant_id:tenant.value,job_type:jtype.value,source:src.value,target:dst.value},'outMigration'); }
function iso(){ return postReq('/api/v1/workshop/iso/build',{profile:profile.value,base_distribution:'debian-trixie',include_tools:['smartmontools','nvme-cli']},'outIso'); }
function jobStatus(){ return getReq('/api/v1/jobs/'+job_id.value,'outJob'); }
</script>
</body></html>
""")
