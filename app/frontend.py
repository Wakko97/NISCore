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
.nav a{display:block;margin-top:8px;padding:10px 12px;border-radius:10px;color:var(--text);text-decoration:none;border:1px solid transparent;transition:.2s ease}
.nav a:hover{border-color:var(--line);background:var(--panel);transform:translateX(2px)}
.main{padding:20px}.top{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}
.token{display:flex;gap:8px;align-items:center}.token input{min-width:280px}
.pill{font-size:12px;padding:6px 10px;border-radius:999px;border:1px solid #35599c;background:#1a2d58;color:#b8d4ff}
.grid{display:grid;gap:12px;margin-top:14px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{background:rgba(16,26,51,.9);border:1px solid var(--line);padding:14px;border-radius:14px;box-shadow:0 10px 24px rgba(0,0,0,.18)}
.card h3{margin:0 0 6px 0;font-size:16px}
.help{margin:0 0 8px 0;font-size:12px;color:var(--muted);line-height:1.35}
label{display:block;font-size:12px;color:var(--muted);margin-top:7px}
input,textarea,select,button{margin-top:4px;width:100%;padding:9px;border-radius:9px;border:1px solid #2f4479;background:var(--panel2);color:white}
input:focus,select:focus,textarea:focus{outline:none;border-color:#5e87ff;box-shadow:0 0 0 3px rgba(94,135,255,.25)}
textarea{min-height:88px;resize:vertical}
button{background:#3257d8;cursor:pointer;font-weight:600;transition:.2s ease} button:hover{filter:brightness(1.07);transform:translateY(-1px)}
.quick{background:#2644ad}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}
pre{white-space:pre-wrap;background:#0a1227;border:1px solid #283a68;border-radius:10px;padding:10px;max-height:220px;overflow:auto;min-height:68px}
.statusbar{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:12px}
.light{background:#0b1530;border:1px solid #2a3f6f;border-radius:10px;padding:8px}
.led{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;background:var(--warn);box-shadow:0 0 8px rgba(255,207,87,.65);animation:pulse 1.4s infinite}
.led.ok{background:var(--ok);box-shadow:0 0 8px rgba(34,195,154,.75)}
.led.err{background:var(--err);box-shadow:0 0 8px rgba(255,107,125,.75)}
@keyframes pulse{0%{opacity:.8}50%{opacity:1}100%{opacity:.8}}
.note{margin-top:10px;font-size:12px;color:#c8d7ff;background:#14254f;border:1px solid #33508d;padding:8px;border-radius:8px}
.searchbar{margin-top:10px;display:grid;grid-template-columns:1fr 160px;gap:8px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}.chip{font-size:12px;padding:6px 10px;border-radius:999px;border:1px solid #35599c;background:#1a2d58;color:#c9dbff;cursor:pointer}
.hidden{display:none!important}
@media(max-width:980px){.layout{grid-template-columns:1fr}.sidebar{border-right:none;border-bottom:1px solid var(--line)}.searchbar{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class='layout'>
  <aside class='sidebar'>
    <div class='brand'>NISCore Console</div>
    <p class='hint'>Moderne Leitoberfläche für Techniker-Einsätze.</p>
    <nav class='nav'>
      <a href='#ops'>1) Start & Diagnose</a>
      <a href='#security'>2) Sicherheit & Löschung</a>
      <a href='#migration'>3) Migration & Images</a>
      <a href='#integrations'>4) Integrationen</a>
      <a href='/docs' target='_blank'>Erweiterte API-Doku</a>
    </nav>
  </aside>
  <main class='main'>
    <div class='top'>
      <div><h1 style='margin:0'>Techniker-Dashboard</h1><div class='hint'>Geführter Ablauf mit Statusleuchten, Direktaktionen und Suche.</div></div>
      <div class='token'><span class='pill'>Anmeldung</span><input id='apiToken' placeholder='JWT Token aus /api/v1/auth/login'></div>
    </div>

    <section class='statusbar'>
      <div class='light'><div><span id='ledSystem' class='led'></span><strong>System</strong></div><div class='hint' id='ledSystemTxt'>noch nicht geprüft</div></div>
      <div class='light'><div><span id='ledReady' class='led'></span><strong>Dienste</strong></div><div class='hint' id='ledReadyTxt'>noch nicht geprüft</div></div>
      <div class='light'><div><span id='ledJobs' class='led'></span><strong>Jobs</strong></div><div class='hint' id='ledJobsTxt'>Status offen</div></div>
    </section>

    <div class='searchbar'>
      <input id='globalSearch' placeholder='Schnellsuche: asset-001, queue-job-id, Hostname ...'>
      <button class='quick' onclick='applyQuickSearch()'>Felder füllen</button>
    </div>
    <div class='chips'>
      <button class='chip' onclick='jumpAndLoad("ops", "/api/v1/clients?limit=20", "outList")'>Zu Clients + laden</button>
      <button class='chip' onclick='jumpAndLoad("migration", "/api/v1/migrations/jobs?limit=20", "outList")'>Zu Migrationen + laden</button>
      <button class='chip' onclick='jumpAndLoad("integrations", "/api/v1/integrations/ndesk/assets?limit=20", "outNdesk")'>NDesk Assets laden</button>
    </div>

    <section class='grid section' id='ops'>
      <article class='card'><h3>Schnellcheck System</h3><p class='help'>Prüft, ob Backend und Dienste betriebsbereit sind.</p><div class='row'><button class='quick' onclick='probe("/health","outSystem","ledSystem","ledSystemTxt")'>System online?</button><button class='quick' onclick='probe("/ready","outSystem","ledReady","ledReadyTxt")'>Dienste bereit?</button></div><pre id='outSystem'></pre></article>
      <article class='card'><h3>Gerät erfassen</h3><p class='help'>Neues Gerät anlegen, bevor Diagnose oder Löschung gestartet wird.</p><label>Geräte-ID (intern)<input id='asset' value='asset-001'></label><label>Seriennummer<input id='serial' value='SN-001'></label><label>Gerätetyp<select id='dtype'><option value='laptop'>Laptop</option><option value='desktop'>Desktop</option><option value='server'>Server</option><option value='tablet'>Tablet</option></select></label><button onclick='registerClient()'>Gerät anlegen</button><pre id='outClient'></pre></article>
      <article class='card'><h3>Diagnose erfassen</h3><p class='help'>Techniker-Ergebnis eintragen. Das System erzeugt daraus Empfehlungen.</p><label>Geräte-ID<input id='d_asset' value='asset-001'></label><label>Techniker-Name<input id='tech' value='alice'></label><label>Diagnose-Ergebnis<select id='result'><option>smart_critical</option><option>malware_indicator</option><option>backup_missing</option></select></label><label>Messdaten / Rohdaten (JSON)<textarea id='raw'>{"temp":72,"health":"critical"}</textarea></label><button onclick='diagnostic()'>Diagnose speichern</button><pre id='outDiag'></pre></article>
    </section>

    <section class='grid section' id='security'>
      <article class='card'><h3>Sicherheitsprüfung Endgerät</h3><p class='help'>Für Vorfälle wie Malware oder verdächtige Prozesse.</p><label>Geräte-ID<input id='sec_asset' value='asset-001'></label><label>Prüfart<select id='sec_type'><option>malware_indicator</option><option>suspicious_activity</option><option>policy_violation</option></select></label><label>Befund / Notiz<textarea id='sec_details'>suspicious process detected</textarea></label><button onclick='endpointCheck()'>Prüfung starten</button><pre id='outSecurity'></pre></article>
      <article class='card'><h3>SSL-Prüfung Website</h3><p class='help'>Prüft Zertifikat und Erreichbarkeit eines Hosts.</p><label>Host<input id='ssl_host' value='example.com'></label><label>Port<input id='ssl_port' value='443'></label><button onclick='sslCheck()'>SSL prüfen</button><pre id='outSsl'></pre></article>
      <article class='card'><h3>Datenlöschung (Wipe)</h3><p class='help'>Startet einen Löschauftrag nach definiertem Standard.</p><label>Geräte-ID<input id='w_asset' value='asset-001'></label><label>Löschmethode<select id='method'><option value='nvme-format'>NVMe Format</option><option value='overwrite'>Overwrite</option></select></label><label>Standard<select id='std'><option value='nist-800-88'>NIST 800-88</option><option value='din-66399'>DIN 66399</option></select></label><button onclick='wipe()'>Löschung starten</button><div class='note'>Hinweis: Vor Löschung immer Sicherung und Freigabe prüfen.</div><pre id='outWipe'></pre></article>
    </section>

    <section class='grid section' id='migration'>
      <article class='card'><h3>Migrationsauftrag</h3><p class='help'>Überträgt Daten zwischen Quell- und Zielsystem.</p><label>Mandant<input id='tenant' value='default'></label><label>Jobtyp<input id='jtype' value='imap'></label><label>Quelle<input id='src' value='imap://legacy'></label><label>Ziel<input id='dst' value='m365://tenant'></label><button onclick='migration()'>Migration starten</button><pre id='outMigration'></pre></article>
      <article class='card'><h3>Werkstatt-ISO bauen</h3><p class='help'>Erstellt ein ISO-Image für Techniker-Tools.</p><label>Profil<select id='profile'><option value='workshop'>Workshop (Standard)</option><option value='forensic'>Forensik</option></select></label><button onclick='iso()'>ISO-Build starten</button><pre id='outIso'></pre></article>
      <article class='card'><h3>Listen & Verlauf</h3><p class='help'>Schnellansicht für angelegte Geräte, Empfehlungen und Migrationsjobs.</p><div class='row'><button onclick='getReq("/api/v1/clients?limit=20","outList")'>Geräte anzeigen</button><button onclick='getReq("/api/v1/recommendations?limit=20","outList")'>Empfehlungen</button></div><button style='margin-top:8px' onclick='getReq("/api/v1/migrations/jobs?limit=20","outList")'>Migrationen anzeigen</button><pre id='outList'></pre></article>
    </section>

    <section class='grid section' id='integrations'>
      <article class='card'><h3>NDesk Asset-Sync</h3><p class='help'>Lädt Asset-Liste aus der NDesk-Integration.</p><button onclick='getReq("/api/v1/integrations/ndesk/assets?limit=20","outNdesk")'>Assets laden</button><pre id='outNdesk'></pre></article>
      <article class='card'><h3>Hintergrundjob prüfen</h3><p class='help'>Status eines gestarteten Jobs anhand der Job-ID abrufen.</p><label>Job-ID<input id='job_id' placeholder='queue-job-id'></label><button onclick='jobStatus()'>Status abrufen</button><pre id='outJob'></pre></article>
    </section>
  </main>
</div>
<script>
function authHeaders(){ const h={"Content-Type":"application/json"}; const t=document.getElementById('apiToken').value.trim(); if(t){h['Authorization']='Bearer '+t;} return h; }
function setLed(ledId, txtId, state, msg){ const led=document.getElementById(ledId); const txt=document.getElementById(txtId); led.className='led'+(state==='ok'?' ok':state==='err'?' err':''); txt.textContent=msg; }
async function render(out, req){ const el=document.getElementById(out); try{ const r=await req; const text=await r.text(); el.textContent=`${r.status} ${r.statusText}\n${text}`; return {status:r.status,text}; }catch(e){ el.textContent='Request error: '+e; return {status:0,text:String(e)}; } }
function getReq(url,out){ return render(out, fetch(url,{headers:authHeaders()})); }
function postReq(url,body,out){ return render(out, fetch(url,{method:'POST',headers:authHeaders(),body:JSON.stringify(body)})); }
async function probe(url,out,ledId,txtId){ const res=await getReq(url,out); if(res.status>=200 && res.status<300){ setLed(ledId,txtId,'ok','OK ('+res.status+')'); } else { setLed(ledId,txtId,'err','Fehler ('+res.status+')'); }}
function registerClient(){ return postReq('/api/v1/clients/register',{tenant_id:'default',asset_id:asset.value,serial_number:serial.value,device_type:dtype.value},'outClient'); }
function diagnostic(){ return postReq('/api/v1/diagnostics/results',{asset_id:d_asset.value,technician:tech.value,result:result.value,raw_json:raw.value||'{}'},'outDiag'); }
function wipe(){ return postReq('/api/v1/wipe/jobs',{asset_id:w_asset.value,method:method.value,standard:std.value},'outWipe'); }
function endpointCheck(){ return postReq('/api/v1/security/endpoint-check',{asset_id:sec_asset.value,scan_type:sec_type.value,details:sec_details.value},'outSecurity'); }
function sslCheck(){ return postReq('/api/v1/web/scans/ssl-check',{host:ssl_host.value,port:parseInt(ssl_port.value||'443',10)},'outSsl'); }
function migration(){ return postReq('/api/v1/migrations/jobs',{tenant_id:tenant.value,job_type:jtype.value,source:src.value,target:dst.value},'outMigration'); }
function iso(){ return postReq('/api/v1/workshop/iso/build',{profile:profile.value,base_distribution:'debian-trixie',include_tools:['smartmontools','nvme-cli']},'outIso'); }
async function jobStatus(){ const id=job_id.value.trim(); const res=await getReq('/api/v1/jobs/'+id,'outJob'); if(id && res.status>=200 && res.status<300){ setLed('ledJobs','ledJobsTxt','ok','Job '+id+' erreichbar'); } else if(id){ setLed('ledJobs','ledJobsTxt','err','Job '+id+' nicht erreichbar'); }}
function applyQuickSearch(){ const v=document.getElementById('globalSearch').value.trim(); if(!v){return;} ['asset','d_asset','sec_asset','w_asset'].forEach(id=>document.getElementById(id).value=v); document.getElementById('job_id').value=v; document.getElementById('ssl_host').value=v.includes('.')?v:document.getElementById('ssl_host').value; }
function jumpAndLoad(anchor,url,out){ document.getElementById(anchor).scrollIntoView({behavior:'smooth',block:'start'}); getReq(url,out); }
</script>
</body></html>
""")
