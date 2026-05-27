from fastapi.responses import HTMLResponse


def admin_html() -> HTMLResponse:
    return HTMLResponse("""
<!doctype html>
<html lang='de'>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width,initial-scale=1'/>
<meta http-equiv='X-Content-Type-Options' content='nosniff'/>
<meta http-equiv='Referrer-Policy' content='no-referrer'/>
<title>NISCore Secure Operations Console</title>
<style>
:root{--bg:#060a16;--bg2:#0f1731;--panel:#111d3c;--line:#2b3f75;--text:#f1f5ff;--muted:#9cb0e1;--accent:#7ca7ff;--ok:#29cc9d;--warn:#ffcc5e;--err:#ff6d7d}
*{box-sizing:border-box}
body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--text);background:radial-gradient(circle at top,#1b2d60,var(--bg) 48%)}
.layout{display:grid;grid-template-columns:320px 1fr;min-height:100vh}
.sidebar{padding:24px;background:rgba(4,9,24,.84);border-right:1px solid var(--line)}
.logo{font-size:24px;font-weight:700;letter-spacing:.3px}
.hint{font-size:12px;color:var(--muted);line-height:1.5}
.kpi{margin-top:12px;padding:12px;border-radius:12px;background:#12244d;border:1px solid #3b5eab}
.kpi strong{display:block;font-size:16px;margin-top:4px}
.main{padding:20px 22px}
.top{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:12px}
.token{display:flex;gap:8px;align-items:center}.token input{min-width:290px}
.pill{padding:7px 10px;border:1px solid #426dc3;border-radius:999px;background:#1a2f63;font-size:12px}
.grid{display:grid;gap:12px}
.grid.cols-2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{padding:15px;border-radius:16px;background:rgba(13,23,48,.92);border:1px solid var(--line);box-shadow:0 12px 26px rgba(0,0,0,.24)}
.card h3{margin:0 0 8px}
input,textarea,select,button{margin-top:5px;width:100%;padding:10px;border-radius:10px;border:1px solid #36508f;background:var(--bg2);color:var(--text)}
button{cursor:pointer;background:#3660de;font-weight:600}
button.alt{background:#294cb6}
button.danger{background:#b83256}
label{font-size:12px;color:var(--muted);display:block;margin-top:8px}
pre{background:#0a1227;border:1px solid #273963;border-radius:11px;padding:10px;min-height:90px;max-height:260px;overflow:auto;white-space:pre-wrap}
.status{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.status span{font-size:12px;border-radius:999px;padding:4px 9px;border:1px solid #3a5697;background:#162753;color:#bad1ff}
.good{border-color:#2d9979!important;background:#12352d!important;color:#baf4e2!important}
.warn{border-color:#a47722!important;background:#3a2c0f!important;color:#ffe7bb!important}
.err{border-color:#a73e50!important;background:#3a1720!important;color:#ffd2dc!important}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.tabs button{width:auto;padding:8px 12px;background:#233f90}
.tabs button.active{background:#3b68e8}
.panel{display:none;margin-top:12px}.panel.active{display:block}
.footer-note{margin-top:10px;padding:10px;border-radius:9px;font-size:12px;border:1px solid #35508d;background:#132449;color:#bfd1ff}
@media(max-width:980px){.layout{grid-template-columns:1fr}.sidebar{border-right:none;border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<div class='layout'>
  <aside class='sidebar'>
    <div class='logo'>NISCore Console</div>
    <p class='hint'>Modular, sicher und unabhängig: Geräteanalyse/Wipe, ISO-Toolkit und Migration sind als getrennte Workspaces aufgebaut.</p>
    <div class='kpi'><span class='hint'>Geräte-Workflow</span><strong>Agent verbinden → Gerät wählen → analysieren/wipen</strong></div>
    <div class='kpi'><span class='hint'>ISO-Tool</span><strong>Eigenes Modul ohne Asset-Abhängigkeit</strong></div>
    <div class='kpi'><span class='hint'>Migration</span><strong>Komplett unabhängig von Geräte-/Asset-Flows</strong></div>
  </aside>

  <main class='main'>
    <div class='top'>
      <div><h1 style='margin:0'>Secure Operations</h1><div class='hint'>Klare Trennung der Module für robuste und wartbare Abläufe.</div></div>
      <div class='token'><span class='pill'>JWT</span><input id='apiToken' placeholder='Bearer Token aus /api/v1/auth/login' autocomplete='off'></div>
    </div>

    <div class='tabs'>
      <button class='active' onclick="switchPanel('panel-device', this)">Geräte via Agent</button>
      <button onclick="switchPanel('panel-iso', this)">ISO Tool</button>
      <button onclick="switchPanel('panel-migration', this)">Migration</button>
      <button onclick="switchPanel('panel-ops', this)">Betriebsstatus</button>
    </div>

    <section id='panel-device' class='panel active card'>
      <h3>Geräteanalyse & Wipe (Agent-Flow)</h3>
      <div class='grid cols-2'>
        <div>
          <label>Asset ID<input id='asset_id' value='asset-001' maxlength='80'></label>
          <label>Seriennummer<input id='serial' value='SN-001' maxlength='120'></label>
          <label>Gerätetyp<select id='dtype'><option>laptop</option><option>desktop</option><option>server</option></select></label>
          <label>Techniker<input id='tech' value='alice' maxlength='80'></label>
          <label>Befund<select id='finding'><option>smart_critical</option><option>malware_indicator</option><option>backup_missing</option></select></label>
          <label><input id='with_wipe' type='checkbox' style='width:auto'> Optional direkt wipen</label>
          <button onclick='runDeviceAnalysis()'>Analysieren / Optional Wipe starten</button>
          <div class='footer-note'>Dieser Flow nutzt den verbundenen Agent-Weg und ist vom ISO-/Migrationstool getrennt.</div>
        </div>
        <div>
          <div class='status'><span id='devState'>Bereit</span></div>
          <pre id='outDevice'></pre>
        </div>
      </div>
    </section>

    <section id='panel-iso' class='panel card'>
      <h3>ISO Build Tool (isoliert)</h3>
      <div class='grid cols-2'>
        <div>
          <label>Profilname<input id='isoProfile' value='fieldkit-secure' maxlength='80'></label>
          <label>Basissystem<select id='isoBase'><option>ubuntu-22.04</option><option>debian-12</option><option>custom-linux</option></select></label>
          <label>Pakete (CSV)<input id='isoPackages' value='smartmontools,nvme-cli,clamav'></label>
          <button onclick='buildIso()'>ISO erstellen</button>
        </div>
        <div><pre id='outIso'></pre></div>
      </div>
    </section>

    <section id='panel-migration' class='panel card'>
      <h3>Migration Suite (asset-unabhängig)</h3>
      <div class='grid cols-2'>
        <div>
          <label>Tenant<input id='migTenant' value='default'></label>
          <label>Quelle<input id='migSrc' value='legacy-system'></label>
          <label>Ziel<input id='migDst' value='niscore-core'></label>
          <label>Datensatzanzahl<input id='migCount' type='number' value='100' min='1'></label>
          <button onclick='createMigration()'>Migration Job anlegen</button>
          <button class='alt' onclick='listMigrations()'>Migration Jobs anzeigen</button>
        </div>
        <div><pre id='outMigration'></pre></div>
      </div>
    </section>

    <section id='panel-ops' class='panel card'>
      <h3>Betriebsstatus & Empfehlungen</h3>
      <div class='grid cols-2'>
        <div><button class='alt' onclick='quickCheck()'>/health + /ready prüfen</button><pre id='outHealth'></pre></div>
        <div><button class='alt' onclick='loadRecommendations()'>Empfehlungen laden</button><pre id='outRecs'></pre></div>
      </div>
    </section>
  </main>
</div>
<script>
function safeValue(v){return (v||'').toString().trim();}
function headers(){const h={"Content-Type":"application/json"};const t=safeValue(apiToken.value);if(t){h.Authorization='Bearer '+t;}return h;}
function state(el,txt,cls=''){el.textContent=txt;el.className=cls;}
async function call(url,method='GET',body=null){const opts={method,headers:headers()};if(body){opts.body=JSON.stringify(body);}const r=await fetch(url,opts);const txt=await r.text();return {ok:r.ok,status:r.status,txt};}
function switchPanel(id,btn){document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));document.getElementById(id).classList.add('active');btn.classList.add('active');}

async function runDeviceAnalysis(){
  state(devState,'Läuft ...','warn');
  const payload={tenant_id:'default',asset_id:safeValue(asset_id.value),serial_number:safeValue(serial.value),device_type:safeValue(dtype.value),technician:safeValue(tech.value),finding:safeValue(finding.value),with_wipe:with_wipe.checked};
  if(!payload.asset_id||!payload.serial_number||!payload.technician){state(devState,'Pflichtfelder fehlen','err');return;}
  const res=await call('/api/v1/missions/run','POST',payload);
  outDevice.textContent='HTTP '+res.status+'\n'+res.txt;
  state(devState,res.ok?'Erfolgreich':'Fehlgeschlagen',res.ok?'good':'err');
}

async function buildIso(){
  const payload={profile_name:safeValue(isoProfile.value),base_system:safeValue(isoBase.value),package_manifest:safeValue(isoPackages.value).split(',').map(x=>x.trim()).filter(Boolean)};
  if(!payload.profile_name){outIso.textContent='Profilname fehlt';return;}
  const res=await call('/api/v1/workshop/iso/build','POST',payload);
  outIso.textContent='HTTP '+res.status+'\n'+res.txt;
}

async function createMigration(){
  const payload={tenant_id:safeValue(migTenant.value),source_system:safeValue(migSrc.value),target_system:safeValue(migDst.value),record_count:parseInt(migCount.value||'0',10)};
  if(!payload.source_system||!payload.target_system||!payload.record_count){outMigration.textContent='Quelle, Ziel und Datensatzanzahl sind Pflicht.';return;}
  const res=await call('/api/v1/migrations/jobs','POST',payload);
  outMigration.textContent='HTTP '+res.status+'\n'+res.txt;
}

async function listMigrations(){const r=await call('/api/v1/migrations/jobs?limit=20');outMigration.textContent='HTTP '+r.status+'\n'+r.txt;}
async function quickCheck(){const h=await call('/health');const r=await call('/ready');outHealth.textContent='/health '+h.status+'\n'+h.txt+'\n\n/ready '+r.status+'\n'+r.txt;}
async function loadRecommendations(){const r=await call('/api/v1/recommendations?limit=20');outRecs.textContent='HTTP '+r.status+'\n'+r.txt;}
</script>
</body></html>
""")
