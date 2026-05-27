from fastapi.responses import HTMLResponse


def admin_html() -> HTMLResponse:
    return HTMLResponse("""
<!doctype html>
<html lang='de'>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width,initial-scale=1'/>
<title>NISCore Mission Control</title>
<style>
:root{--bg:#070b17;--panel:#101a33;--panel2:#0d152c;--line:#243666;--text:#ecf0ff;--muted:#9aabd8;--accent:#7aa2ff;--ok:#22c39a;--warn:#ffcf57;--err:#ff6b7d}
*{box-sizing:border-box}
body{margin:0;font-family:Inter,Arial,sans-serif;background:linear-gradient(165deg,#070b17,#0f1a38 65%);color:var(--text)}
.layout{display:grid;grid-template-columns:300px 1fr;min-height:100vh}
.sidebar{padding:22px;border-right:1px solid var(--line);background:rgba(4,9,22,.75)}
.brand{font-size:22px;font-weight:700}
.hint{font-size:12px;color:var(--muted);line-height:1.4}
.kpi{margin-top:14px;padding:10px;border-radius:10px;background:#14254f;border:1px solid #35599c}
.kpi strong{display:block;font-size:18px}
.main{padding:20px}
.top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.token{display:flex;gap:8px;align-items:center}.token input{min-width:280px}
.pill{font-size:12px;padding:6px 10px;border-radius:999px;border:1px solid #35599c;background:#1a2d58;color:#b8d4ff}
.card{background:rgba(16,26,51,.93);border:1px solid var(--line);padding:14px;border-radius:14px;box-shadow:0 10px 24px rgba(0,0,0,.2)}
.card h3{margin:0 0 8px}
.grid{display:grid;gap:12px;margin-top:14px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
input,textarea,select,button{margin-top:4px;width:100%;padding:9px;border-radius:9px;border:1px solid #2f4479;background:var(--panel2);color:white}
button{background:#3257d8;cursor:pointer;font-weight:600}
button.alt{background:#2644ad}
label{display:block;font-size:12px;color:var(--muted);margin-top:7px}
pre{white-space:pre-wrap;background:#0a1227;border:1px solid #283a68;border-radius:10px;padding:10px;max-height:260px;overflow:auto;min-height:90px}
.steps{display:grid;gap:8px;margin-top:8px}
.step{display:flex;gap:8px;align-items:center;padding:8px;border-radius:10px;background:#0f1a37;border:1px solid #2b3f72}
.badge{width:24px;height:24px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;background:#1a2d58}
.step.done{border-color:#2a8f6f;background:#112f2a}
.step.active{border-color:#557ff2;background:#14254f}
.alert{font-size:13px;padding:10px;border-radius:8px;margin-top:10px;border:1px solid #32508d;background:#122347}
@media(max-width:980px){.layout{grid-template-columns:1fr}.sidebar{border-right:none;border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<div class='layout'>
  <aside class='sidebar'>
    <div class='brand'>NISCore Mission Control</div>
    <p class='hint'>Neukonzipiert als geführte Einsatzkonsole: ein Ticket/Asset durchläuft klar definierte Phasen statt unübersichtlicher API-Einzelschritte.</p>
    <div class='kpi'><span class='hint'>Ablaufmodell</span><strong>Intake → Analyse → Entscheidung → Ausführung → Abschluss</strong></div>
    <div class='kpi'><span class='hint'>Wertversprechen</span><strong>Schneller zum sicheren, dokumentierten Ergebnis</strong></div>
  </aside>
  <main class='main'>
    <div class='top'>
      <div><h1 style='margin:0'>Einsatzsteuerung</h1><div class='hint'>Die Oberfläche fokussiert auf den realen Arbeitsablauf eines Techniker-Einsatzes.</div></div>
      <div class='token'><span class='pill'>JWT</span><input id='apiToken' placeholder='Bearer Token aus /api/v1/auth/login'></div>
    </div>

    <section class='card'>
      <h3>1) Geführter Einsatz (neu)</h3>
      <p class='hint'>Du gibst nur Asset + Befund ein. Das System führt durch den vollständigen End-to-End-Flow inkl. Empfehlung, optionaler Löschung und Zertifikat.</p>
      <div class='grid'>
        <div>
          <label>Asset ID<input id='asset_id' value='asset-001'></label>
          <label>Seriennummer<input id='serial' value='SN-001'></label>
          <label>Gerätetyp<select id='dtype'><option>laptop</option><option>desktop</option><option>server</option></select></label>
          <label>Befund<select id='finding'><option>smart_critical</option><option>malware_indicator</option><option>backup_missing</option></select></label>
          <label>Techniker<input id='tech' value='alice'></label>
          <label><input id='with_wipe' type='checkbox' checked style='width:auto'> Löschung direkt mitausführen</label>
          <button onclick='runMission()'>Einsatz komplett ausführen</button>
          <div class='alert'>Tipp: Der Ablauf läuft serverseitig atomar über einen Mission-Endpunkt.</div>
        </div>
        <div>
          <div class='steps'>
            <div id='s1' class='step'><span class='badge'>1</span>Intake: Gerät registrieren</div>
            <div id='s2' class='step'><span class='badge'>2</span>Analyse: Diagnose erfassen</div>
            <div id='s3' class='step'><span class='badge'>3</span>Entscheidung: Empfehlung laden</div>
            <div id='s4' class='step'><span class='badge'>4</span>Ausführung: Wipe (optional)</div>
            <div id='s5' class='step'><span class='badge'>5</span>Abschluss: Audit/Ergebnis</div>
          </div>
        </div>
      </div>
      <pre id='outMission'></pre>
    </section>

    <section class='grid'>
      <article class='card'>
        <h3>2) Betriebsstatus</h3>
        <button class='alt' onclick='quickCheck()'>/health + /ready prüfen</button>
        <pre id='outHealth'></pre>
      </article>
      <article class='card'>
        <h3>3) Verlauf / Recommendations</h3>
        <button class='alt' onclick='loadRecommendations()'>Empfehlungen laden</button>
        <pre id='outRecs'></pre>
      </article>
    </section>
  </main>
</div>
<script>
function headers(){const h={"Content-Type":"application/json"};const t=apiToken.value.trim();if(t){h.Authorization='Bearer '+t;}return h;}
function mark(step,state){const el=document.getElementById(step);el.className='step '+state;}
function resetSteps(){['s1','s2','s3','s4','s5'].forEach(s=>mark(s,''));}
async function call(url,method='GET',body=null){const opts={method,headers:headers()};if(body){opts.body=JSON.stringify(body);}const r=await fetch(url,opts);const txt=await r.text();return {ok:r.ok,status:r.status,txt};}

async function runMission(){
  resetSteps();
  mark('s1','active'); mark('s2','active'); mark('s3','active'); if(with_wipe.checked){mark('s4','active');} mark('s5','active');
  const payload={tenant_id:'default',asset_id:asset_id.value,serial_number:serial.value,device_type:dtype.value,technician:tech.value,finding:finding.value,with_wipe:with_wipe.checked};
  const res=await call('/api/v1/missions/run','POST',payload);
  if(!res.ok){ outMission.textContent='Mission fehlgeschlagen ('+res.status+')\n'+res.txt; return; }
  mark('s1','done'); mark('s2','done'); mark('s3','done'); mark('s5','done'); if(with_wipe.checked){mark('s4','done');} else {mark('s4','done');}
  outMission.textContent='Mission erfolgreich ('+res.status+')\n'+res.txt;
}

async function quickCheck(){const h=await call('/health'); const r=await call('/ready'); outHealth.textContent='/health '+h.status+'\n'+h.txt+'\n\n/ready '+r.status+'\n'+r.txt;}
async function loadRecommendations(){const r=await call('/api/v1/recommendations?limit=20'); outRecs.textContent=r.status+'\n'+r.txt;}
</script>
</body></html>
""")
