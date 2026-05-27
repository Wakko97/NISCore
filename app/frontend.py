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
:root{--bg:#070b17;--bg2:#101938;--panel:#101c3b;--line:#2c3f77;--text:#eef3ff;--muted:#98acdf;--accent:#7ea9ff;--ok:#27c99a;--warn:#f5bb4f;--err:#f26779}
*{box-sizing:border-box}
body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--text);background:radial-gradient(circle at top,#1b2d61,var(--bg) 52%)}
.layout{display:grid;grid-template-columns:320px 1fr;min-height:100vh}
.sidebar{padding:24px;background:rgba(6,10,24,.88);border-right:1px solid var(--line)}
.logo{font-size:24px;font-weight:700}.hint{font-size:12px;color:var(--muted);line-height:1.5}
.kpi{margin-top:12px;padding:12px;border-radius:12px;background:#132550;border:1px solid #3a5daa}.kpi strong{display:block;font-size:15px;margin-top:4px}
.main{padding:20px 22px}
.top{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:10px}
.token{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.token input{min-width:220px}
.pill{padding:7px 10px;border:1px solid #426dc3;border-radius:999px;background:#1a2f63;font-size:12px}
.grid{display:grid;gap:12px}.grid.cols-2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{padding:15px;border-radius:16px;background:rgba(13,23,49,.93);border:1px solid var(--line);box-shadow:0 12px 24px rgba(0,0,0,.26)}
.card h3{margin:0 0 8px}
input,textarea,select,button{margin-top:5px;width:100%;padding:10px;border-radius:10px;border:1px solid #36508f;background:var(--bg2);color:var(--text)}
button{cursor:pointer;background:#3660de;font-weight:600}
button:hover{filter:brightness(1.08)} button:disabled{opacity:.58;cursor:not-allowed}
button.alt{background:#2a4eb9}button.danger{background:#b83356}button.ghost{background:#1a2d5f}
label{font-size:12px;color:var(--muted);display:block;margin-top:8px}
pre{background:#0a1227;border:1px solid #273963;border-radius:11px;padding:10px;min-height:110px;max-height:280px;overflow:auto;white-space:pre-wrap}
.status{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.status span{font-size:12px;border-radius:999px;padding:4px 9px;border:1px solid #3a5697;background:#162753;color:#bad1ff}
.good{border-color:#2d9979!important;background:#12352d!important;color:#baf4e2!important}.warn{border-color:#a47722!important;background:#3a2c0f!important;color:#ffe7bb!important}.err{border-color:#a73e50!important;background:#3a1720!important;color:#ffd2dc!important}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}.tabs button{width:auto;padding:8px 12px;background:#233f90}.tabs button.active{background:#3b68e8}
.panel{display:none;margin-top:12px}.panel.active{display:block}
.inline-row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.footer-note{margin-top:10px;padding:10px;border-radius:9px;font-size:12px;border:1px solid #35508d;background:#132449;color:#bfd1ff}
@media(max-width:980px){.layout{grid-template-columns:1fr}.sidebar{border-right:none;border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<div class='layout'>
  <aside class='sidebar'>
    <div class='logo'>NISCore Console</div>
    <p class='hint'>Modernisierte Operations-Konsole: klickbar, nutzbar, klar getrennte Flows.</p>
    <div class='kpi'><span class='hint'>Geräte-Workflow</span><strong>Agent verbinden → Mission starten → Ergebnis sehen</strong></div>
    <div class='kpi'><span class='hint'>ISO-Tool</span><strong>Profil setzen, Pakete wählen, Build triggern</strong></div>
    <div class='kpi'><span class='hint'>Migration</span><strong>Job erstellen, Verlauf laden, schnell wiederholen</strong></div>
  </aside>

  <main class='main'>
    <div class='top'>
      <div><h1 style='margin:0'>Secure Operations</h1><div class='hint'>Alle Elemente aktiv nutzbar inklusive Quick-Actions und Persistenz.</div></div>
      <div class='token'>
        <span class='pill'>JWT</span>
        <input id='apiToken' placeholder='Bearer Token aus /api/v1/auth/login' autocomplete='off'>
        <button type='button' class='alt' style='width:auto;margin-top:0' onclick='saveToken()'>Token speichern</button>
        <button type='button' class='danger' style='width:auto;margin-top:0' onclick='clearToken()'>Token löschen</button>
      </div>
    </div>

    <section class='card' style='margin-top:12px'>
      <h3>API Verbindung & Session</h3>
      <div class='grid cols-2'>
        <div>
          <label>API Basis-URL<input id='apiBase' value='' placeholder='leer = gleiche Domain'></label>
          <div class='inline-row'>
            <button class='alt' onclick='checkConnection()'>Verbindung prüfen</button>
            <button class='ghost' onclick='autoLoginDemo()'>Demo-Login ausführen</button>
          </div>
          <div class='footer-note'>URL + Token werden lokal gespeichert. Jeder API-Aufruf nutzt die gewählte Basis-URL.</div>
        </div>
        <div>
          <div class='status'><span id='connState'>Nicht geprüft</span><span id='busyState'>Idle</span></div>
          <pre id='outConn'></pre>
        </div>
      </div>
    </section>

    <div class='tabs'>
      <button class='active' onclick="switchPanel('panel-device', this)">Geräte via Agent</button>
      <button onclick="switchPanel('panel-iso', this)">ISO Tool</button>
      <button onclick="switchPanel('panel-migration', this)">Migration</button>
      <button onclick="switchPanel('panel-ops', this)">Betriebsstatus</button>
      <button onclick="switchPanel('panel-settings', this)">Einstellungen</button>
    </div>

    <section id='panel-device' class='panel active card'>
      <h3>Geräteanalyse & Wipe (Agent-Flow)</h3>
      <div class='grid cols-2'>
        <div>
          <label>Tenant ID<input id='tenant_id' value='default' maxlength='80'></label>
          <label>Asset ID<input id='asset_id' value='asset-001' maxlength='80'></label>
          <label>Seriennummer<input id='serial' value='SN-001' maxlength='120'></label>
          <label>Gerätetyp<select id='dtype'><option>laptop</option><option>desktop</option><option>server</option></select></label>
          <label>Techniker<input id='tech' value='alice' maxlength='80'></label>
          <label>Befund<select id='finding'><option>smart_critical</option><option>malware_indicator</option><option>backup_missing</option></select></label>
          <label><input id='with_wipe' type='checkbox' style='width:auto'> Optional direkt wipen</label>
          <div class='inline-row'>
            <button onclick='runDeviceAnalysis()'>Mission starten</button>
            <button class='ghost' onclick='fillDevicePreset()'>Preset laden</button>
          </div>
        </div>
        <div>
          <div class='status'><span id='devState'>Bereit</span></div>
          <pre id='outDevice'></pre>
        </div>
      </div>
    </section>

    <section id='panel-iso' class='panel card'>
      <h3>ISO Build Tool</h3>
      <div class='grid cols-2'>
        <div>
          <label>Profilname<input id='isoProfile' value='fieldkit-secure' maxlength='80'></label>
          <label>Basissystem<select id='isoBase'><option>ubuntu-22.04</option><option>debian-12</option><option>custom-linux</option></select></label>
          <label>Pakete (CSV)<input id='isoPackages' value='smartmontools,nvme-cli,clamav'></label>
          <div class='inline-row'><button onclick='buildIso()'>ISO erstellen</button><button class='ghost' onclick='fillIsoPreset()'>Preset laden</button></div>
        </div>
        <div><pre id='outIso'></pre></div>
      </div>
    </section>

    <section id='panel-migration' class='panel card'>
      <h3>Migration Suite</h3>
      <div class='grid cols-2'>
        <div>
          <label>Tenant<input id='migTenant' value='default'></label>
          <label>Quelle<input id='migSrc' value='legacy-system'></label>
          <label>Ziel<input id='migDst' value='niscore-core'></label>
          <label>Datensatzanzahl<input id='migCount' type='number' value='100' min='1'></label>
          <div class='inline-row'>
            <button onclick='createMigration()'>Migration Job anlegen</button>
            <button class='alt' onclick='listMigrations()'>Migration Jobs anzeigen</button>
          </div>
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

    <section id='panel-settings' class='panel card'>
      <h3>Einstellungen</h3>
      <div class='grid cols-2'>
        <div>
          <label>Theme<select id='setTheme'><option value='dark'>Dark</option><option value='contrast'>High Contrast</option></select></label>
          <label>Sprache<select id='setLang'><option value='de'>Deutsch</option><option value='en'>English</option></select></label>
          <label>Standard Tenant<input id='setTenant' value='default' maxlength='80'></label>
          <label>Standard Limit Empfehlungen<input id='setRecLimit' type='number' min='1' max='200' value='20'></label>
          <div class='inline-row'>
            <button onclick='saveSettings()'>Einstellungen speichern</button>
            <button class='danger' onclick='resetSettings()'>Auf Standard zurücksetzen</button>
          </div>
          <div class='inline-row'>
            <button class='ghost' onclick='exportSettings()'>Exportieren</button>
            <button class='ghost' onclick='importSettings()'>Importieren</button>
          </div>
        </div>
        <div>
          <div class='status'><span id='settingsState'>Nicht gespeichert</span></div>
          <pre id='outSettings'></pre>
        </div>
      </div>
    </section>

  </main>
</div>
<script>
const ui={
  get token(){return document.getElementById('apiToken')}, get base(){return document.getElementById('apiBase')},
  get busy(){return document.getElementById('busyState')}, get conn(){return document.getElementById('connState')}
};
function q(id){return document.getElementById(id);} function safeValue(v){return (v||'').toString().trim();}
function baseUrl(){return safeValue(ui.base.value).replace(/\\/$/, '');}
function headers(){const h={'Content-Type':'application/json'};const t=safeValue(ui.token.value);if(t){h.Authorization='Bearer '+t;}return h;}
function state(el,txt,cls=''){el.textContent=txt;el.className=cls;}
function setBusy(on){state(ui.busy,on?'Beschäftigt':'Idle',on?'warn':'');document.querySelectorAll('button').forEach(b=>b.disabled=on&&!(b.classList.contains('active')));}
function show(el,msg,obj){el.textContent=msg+(obj?('\n'+JSON.stringify(obj,null,2)):'' );}
async function call(url,method='GET',body=null){
  const opts={method,headers:headers()}; if(body){opts.body=JSON.stringify(body);} const target=(baseUrl()?baseUrl():'')+url;
  try{const r=await fetch(target,opts);const txt=await r.text();let parsed=null;try{parsed=JSON.parse(txt);}catch(_){parsed=txt;}return {ok:r.ok,status:r.status,txt,parsed,target};}
  catch(err){return {ok:false,status:0,txt:'Netzwerkfehler: '+(err?.message||String(err)),parsed:null,target};}
}
function switchPanel(id,btn){document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));q(id).classList.add('active');btn.classList.add('active');}
function saveToken(){localStorage.setItem('niscore_token',safeValue(ui.token.value));localStorage.setItem('niscore_base',safeValue(ui.base.value));state(ui.conn,'Token/URL gespeichert','good');}
function clearToken(){ui.token.value='';localStorage.removeItem('niscore_token');state(ui.conn,'Token gelöscht','warn');}
function hydrate(){ui.token.value=localStorage.getItem('niscore_token')||'';ui.base.value=localStorage.getItem('niscore_base')||'';}

async function checkConnection(){setBusy(true);state(ui.conn,'Prüfung läuft ...','warn');const h=await call('/health');show(q('outConn'),'URL: '+h.target+'\nHTTP '+h.status,h.parsed);state(ui.conn,h.ok?'Verbindung OK':'Verbindung fehlgeschlagen',h.ok?'good':'err');setBusy(false);}
async function autoLoginDemo(){show(q('outConn'),'Demo-Login ist projektspezifisch. Bitte /api/v1/auth/login mit echten Zugangsdaten nutzen.');}
function fillDevicePreset(){q('tenant_id').value='default';q('asset_id').value='asset-ops-009';q('serial').value='SN-OPS-009';q('dtype').value='laptop';q('tech').value='ops-admin';q('finding').value='smart_critical';q('with_wipe').checked=false;state(q('devState'),'Preset geladen','good');}
function fillIsoPreset(){q('isoProfile').value='incident-response-kit';q('isoBase').value='ubuntu-22.04';q('isoPackages').value='smartmontools,nvme-cli,clamav,wipe';show(q('outIso'),'ISO Preset geladen.');}

async function runDeviceAnalysis(){
  setBusy(true);state(q('devState'),'Läuft ...','warn');
  const payload={tenant_id:safeValue(q('tenant_id').value),asset_id:safeValue(q('asset_id').value),serial_number:safeValue(q('serial').value),device_type:safeValue(q('dtype').value),technician:safeValue(q('tech').value),finding:safeValue(q('finding').value),with_wipe:q('with_wipe').checked};
  if(!payload.tenant_id||!payload.asset_id||!payload.serial_number||!payload.technician){state(q('devState'),'Pflichtfelder fehlen','err');setBusy(false);return;}
  const res=await call('/api/v1/missions/run','POST',payload);show(q('outDevice'),'HTTP '+res.status,res.parsed||res.txt);state(q('devState'),res.ok?'Erfolgreich':'Fehlgeschlagen',res.ok?'good':'err');setBusy(false);
}
async function buildIso(){setBusy(true);const payload={profile_name:safeValue(q('isoProfile').value),base_system:safeValue(q('isoBase').value),package_manifest:safeValue(q('isoPackages').value).split(',').map(x=>x.trim()).filter(Boolean)};if(!payload.profile_name){show(q('outIso'),'Profilname fehlt');setBusy(false);return;}const res=await call('/api/v1/workshop/iso/build','POST',payload);show(q('outIso'),'HTTP '+res.status,res.parsed||res.txt);setBusy(false);}
async function createMigration(){setBusy(true);const payload={tenant_id:safeValue(q('migTenant').value),source_system:safeValue(q('migSrc').value),target_system:safeValue(q('migDst').value),record_count:parseInt(q('migCount').value||'0',10)};if(!payload.source_system||!payload.target_system||!payload.record_count){show(q('outMigration'),'Quelle, Ziel und Datensatzanzahl sind Pflicht.');setBusy(false);return;}const res=await call('/api/v1/migrations/jobs','POST',payload);show(q('outMigration'),'HTTP '+res.status,res.parsed||res.txt);setBusy(false);}
async function listMigrations(){setBusy(true);const r=await call('/api/v1/migrations/jobs?limit=20');show(q('outMigration'),'HTTP '+r.status,r.parsed||r.txt);setBusy(false);}
async function quickCheck(){setBusy(true);const h=await call('/health');const r=await call('/ready');show(q('outHealth'),'/health '+h.status+'\n/ready '+r.status,{health:h.parsed,ready:r.parsed});setBusy(false);}
async function loadRecommendations(){setBusy(true);const limit=Math.max(1,parseInt(q('setRecLimit').value||'20',10));const r=await call('/api/v1/recommendations?limit='+limit);show(q('outRecs'),'HTTP '+r.status,r.parsed||r.txt);setBusy(false);}



const defaultSettings={theme:'dark',lang:'de',tenant:'default',rec_limit:20};
function currentSettings(){return {theme:safeValue(q('setTheme').value),lang:safeValue(q('setLang').value),tenant:safeValue(q('setTenant').value),rec_limit:parseInt(q('setRecLimit').value||'20',10)};}
function applySettings(cfg){
  const c={...defaultSettings,...(cfg||{})};
  q('setTheme').value=c.theme; q('setLang').value=c.lang; q('setTenant').value=c.tenant; q('setRecLimit').value=String(c.rec_limit);
  document.documentElement.dataset.theme=c.theme;
  q('tenant_id').value=c.tenant; q('migTenant').value=c.tenant;
  state(q('settingsState'),'Einstellungen geladen','good');
}
function saveSettings(){const cfg=currentSettings(); localStorage.setItem('niscore_settings',JSON.stringify(cfg)); applySettings(cfg); show(q('outSettings'),'Gespeichert',cfg);}
function loadSettings(){try{const raw=localStorage.getItem('niscore_settings'); if(!raw){applySettings(defaultSettings); return;} applySettings(JSON.parse(raw));}catch(_){applySettings(defaultSettings);}}
function resetSettings(){localStorage.removeItem('niscore_settings'); applySettings(defaultSettings); state(q('settingsState'),'Auf Standard zurückgesetzt','warn'); show(q('outSettings'),'Standardwerte aktiv',defaultSettings);}
function exportSettings(){const cfg=currentSettings(); show(q('outSettings'),'Export (JSON kopieren):',cfg);}
function importSettings(){const raw=prompt('Settings JSON einfügen'); if(!raw){return;} try{const cfg=JSON.parse(raw); localStorage.setItem('niscore_settings',JSON.stringify(cfg)); applySettings(cfg); show(q('outSettings'),'Import erfolgreich',cfg);}catch(e){state(q('settingsState'),'Import fehlgeschlagen','err'); show(q('outSettings'),'Ungültiges JSON',{error:String(e)});}}

hydrate();
loadSettings();
</script>
</body></html>
""")
