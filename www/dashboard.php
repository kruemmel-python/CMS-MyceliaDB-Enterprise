<?php
require_once __DIR__ . '/bootstrap.php';
require_login();
$status = call_mycelia('security_evolution_status', engine_session_context());
$telemetry = call_mycelia('telemetry_snapshot', ['limit' => 32] + engine_session_context());
layout_header('Kognitives Live-Dashboard');
?>
<section class="card">
  <h1>Kognitives Live-Dashboard</h1>
  <p>Aggregierte Mycelia-Telemetrie ohne Nutzdaten: Harmony, Tension, VRAM-Pfade, Node-Zahl und Ereignisse.</p>
  <pre id="telemetry-json"><?= e(json_encode($telemetry, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) ?></pre>
</section>
<section class="grid">
  <article class="card"><h2>Enterprise Evolution</h2><pre><?= e(json_encode($status['features'] ?? $status, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) ?></pre></article>
  <article class="card"><h2>Live-Feld</h2><canvas id="mycelia-field" width="640" height="320" style="width:100%;border-radius:16px;background:#090b10"></canvas></article>
</section>
<script>
async function refreshTelemetry(){
  const res = await fetch('telemetry_api.php?limit=64', {credentials:'same-origin'});
  let data = null; try { data = await res.json(); } catch(e) { return; }
  const pre = document.getElementById('telemetry-json'); if(pre) pre.textContent = JSON.stringify(data,null,2);
  const c = document.getElementById('mycelia-field'); const ctx = c.getContext('2d');
  ctx.clearRect(0,0,c.width,c.height);
  const events = (data.events||[]).slice(-64);
  for(let i=0;i<events.length;i++){
    const e=events[i]; const x=(i/64)*c.width; const h=Math.max(4, (e.tension||0)*c.height*2);
    ctx.fillRect(x, c.height-h, 8, h);
    ctx.fillText((e.event||'').slice(0,8), x, c.height-h-4);
  }
}
setInterval(refreshTelemetry, 2500);
</script>
<?php layout_footer(); ?>
