from fastapi.responses import HTMLResponse


def admin_html() -> HTMLResponse:
    return HTMLResponse("""
<!doctype html>
<html lang='de'>
<head>
<meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/>
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
""")
