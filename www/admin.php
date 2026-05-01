<?php
require_once __DIR__ . '/bootstrap.php';
require_admin();

$audit = $_SESSION['_last_vram_audit'] ?? null;
$manifest = $_SESSION['_last_residency_manifest'] ?? null;
$probeSubmit = $_SESSION['_last_probe_submit'] ?? null;
$nativeReport = $_SESSION['_last_native_gpu_report'] ?? null;
$strictCert = $_SESSION['_last_strict_vram_cert'] ?? null;
$evidenceBundle = $_SESSION['_last_vram_evidence_bundle'] ?? null;
$enterpriseReport = $_SESSION['_last_enterprise_v120'] ?? null;
unset($_SESSION['_last_vram_audit'], $_SESSION['_last_residency_manifest'], $_SESSION['_last_probe_submit'], $_SESSION['_last_native_gpu_report'], $_SESSION['_last_strict_vram_cert'], $_SESSION['_last_vram_evidence_bundle'], $_SESSION['_last_enterprise_v120']);

if (!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])) {
    $op = strval($_POST['direct_op']);
    $response = call_mycelia_direct_ingest($op, strval($_POST['sealed_ingest']), direct_actor_context());
    if ($op === 'vram_residency_audit') {
        $_SESSION['_last_vram_audit'] = $response;
    }
    $okMessage = match ($op) {
        'admin_set_site_text' => 'Webseitentext wurde im Mycelia-CMS gespeichert.',
        'admin_update_user_rights' => 'Benutzerrechte wurden in MyceliaDB aktualisiert.',
        'admin_install_plugin' => 'Plugin-Attraktor wurde installiert.',
        'admin_set_plugin_state' => 'Plugin-Status wurde geändert.',
        'admin_delete_plugin' => 'Plugin-Attraktor wurde gelöscht.',
        'run_plugin' => 'Plugin wurde in der Capability-Sandbox ausgeführt.',
        default => 'Direct GPU Ingest Admin-Aktion verarbeitet.',
    };
    flash(($response['status'] ?? '') === 'ok' ? $okMessage : ($response['message'] ?? 'Admin-Aktion fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('admin.php');
}

if (isset($_POST['run_residency_manifest'])) {
    $_SESSION['_last_residency_manifest'] = call_mycelia('residency_audit_manifest', []);
    redirect('admin.php');
}

if (isset($_POST['submit_memory_probe_report'])) {
    $json = strval($_POST['memory_probe_json'] ?? '');
    $report = json_decode($json, true);
    if (!is_array($report)) {
        flash('Memory-Probe-Report ist kein gültiges JSON.', 'error');
        redirect('admin.php');
    }
    $_SESSION['_last_probe_submit'] = call_mycelia('submit_external_memory_probe', $report);
    $_SESSION['_last_native_gpu_report'] = call_mycelia('native_gpu_capability_report', []);
    $_SESSION['_last_strict_vram_cert'] = call_mycelia('strict_vram_certification', []);
    $_SESSION['_last_vram_evidence_bundle'] = call_mycelia('strict_vram_evidence_bundle', []);
    redirect('admin.php');
}

if (isset($_POST['run_restore_residency_audit'])) {
    $_SESSION['_last_vram_audit'] = call_mycelia('restore_snapshot_residency_audit', [
        'path' => 'snapshots/autosave.mycelia'
    ]);
    redirect('admin.php');
}

if (isset($_POST['run_native_gpu_report'])) {
    $_SESSION['_last_native_gpu_report'] = call_mycelia('native_gpu_capability_report', []);
    redirect('admin.php');
}

if (isset($_POST['run_enterprise_v120_report'])) {
    $_SESSION['_last_enterprise_v120'] = [
        'smql_explain' => call_mycelia('smql_explain', ['query' => strval($_POST['smql_query'] ?? 'FIND * LIMIT 10')]),
        'smql_query' => call_mycelia('smql_query', ['query' => strval($_POST['smql_query'] ?? 'FIND * LIMIT 10')]),
        'federation_status' => call_mycelia('federation_status', []),
        'provenance_verify' => call_mycelia('provenance_verify', []),
        'provenance_log' => call_mycelia('provenance_log', ['limit' => 25]),
        'native_library_authenticity' => call_mycelia('native_library_authenticity', []),
        'local_transport_security_status' => call_mycelia('local_transport_security_status', []),
        'quantum_guard_status' => call_mycelia('quantum_guard_status', []),
    ];
    redirect('admin.php');
}

if (isset($_POST['run_native_gpu_selftest'])) {
    $_SESSION['_last_native_gpu_report'] = call_mycelia('native_gpu_residency_selftest', []);
    $_SESSION['_last_vram_evidence_bundle'] = call_mycelia('strict_vram_evidence_bundle', []);
    redirect('admin.php');
}

if (isset($_POST['run_strict_certification'])) {
    $_SESSION['_last_strict_vram_cert'] = call_mycelia('strict_vram_certification', []);
    $_SESSION['_last_vram_evidence_bundle'] = call_mycelia('strict_vram_evidence_bundle', []);
    redirect('admin.php');
}

if (isset($_POST['run_vram_evidence_bundle'])) {
    $_SESSION['_last_vram_evidence_bundle'] = call_mycelia('strict_vram_evidence_bundle', []);
    $_SESSION['_last_strict_vram_cert'] = $_SESSION['_last_vram_evidence_bundle']['strict_vram_certification'] ?? null;
    $_SESSION['_last_native_gpu_report'] = $_SESSION['_last_vram_evidence_bundle']['native_gpu_capability_report'] ?? null;
    redirect('admin.php');
}

if (isset($_POST['run_vram_audit'])) {
    // Legacy/diagnostic: sending probes here intentionally materializes them in Python.
    // For a real CPU-RAM proof use residency_audit_manifest + external memory probe.
    $probeText = strval($_POST['probes'] ?? '');
    $probes = array_values(array_filter(array_map('trim', preg_split('/[\r\n,]+/', $probeText))));
    $audit = call_mycelia('vram_residency_audit', [
        'probes' => $probes,
        'create_temp_snapshot' => true
    ]);
}

if (isset($_POST['delete_thread'])) call_mycelia('delete_forum_thread', array_merge(actor_payload(), ['signature' => $_POST['signature'] ?? '']));
if (isset($_POST['delete_blog'])) call_mycelia('delete_blog', array_merge(actor_payload(), ['signature' => $_POST['signature'] ?? '']));
if (isset($_POST['delete_post'])) call_mycelia('delete_blog_post', array_merge(actor_payload(), ['signature' => $_POST['signature'] ?? '']));
if (isset($_POST['delete_comment'])) call_mycelia('delete_comment', array_merge(actor_payload(), ['signature' => $_POST['signature'] ?? '']));
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !isset($_POST['run_vram_audit'])) {
    flash('Admin-Aktion ausgeführt und im Mycelia-Autosnapshot persistiert.', 'info');
    redirect('admin.php');
}
$overview = require_mycelia_ok(call_mycelia('admin_overview', []));
$heartbeatStatus = call_mycelia('heartbeat_audit_status', []);
layout_header(txt('admin.title'));
?>
<section class="panel">
    <h1><?= e(txt('admin.title')) ?></h1>
    <p class="muted"><?= e(txt('admin.subtitle')) ?></p><p><a class="button secondary" href="plugins.php"><?= e(txt('plugins.title')) ?></a></p>
    <div class="kpi">
        <div><strong><?= e(count($overview['forum_threads'] ?? [])) ?></strong><span>Threads</span></div>
        <div><strong><?= e(count($overview['blogs'] ?? [])) ?></strong><span>Blogs</span></div>
        <div><strong><?= e(count($overview['blog_posts'] ?? [])) ?></strong><span>Blogposts</span></div>
        <div><strong><?= e(count($overview['comments'] ?? [])) ?></strong><span>Kommentare</span></div>
    </div>
</section>

<section class="panel" style="margin-top:22px">
    <h2><?= e(txt('admin.texts_title')) ?></h2>
    <p class="muted">Alle registrierten UI-Texte können hier geändert werden. Die Overrides liegen als verschlüsselte <code>mycelia_site_texts</code>-Attraktoren im Autosnapshot.</p>
    <table class="table">
        <tr><th>Schlüssel</th><th>Aktueller Text</th><th>Aktion</th></tr>
        <?php
        $textOverrides = $overview['site_texts'] ?? [];
        foreach (site_text_catalog() as $key => $defaultValue):
            $currentValue = is_array($textOverrides) && isset($textOverrides[$key]['value']) ? mycelia_scalar_text($textOverrides[$key]['value']) : mycelia_scalar_text($defaultValue);
        ?>
            <tr>
                <td class="mono"><?= e($key) ?></td>
                <td>
                    <form method="post" data-direct-op="admin_set_site_text" class="inline-form">
                        <input type="hidden" name="key" value="<?= e($key) ?>">
                        <input type="hidden" name="context" value="web">
                        <textarea name="value" rows="2"><?= e($currentValue) ?></textarea>
                        <button name="save_text"><?= e(txt('admin.save_text')) ?></button>
                    </form>
                </td>
                <td class="muted">Default: <?= e(ui_excerpt($defaultValue, 90)) ?></td>
            </tr>
        <?php endforeach; ?>
    </table>
</section>

<section class="panel" style="margin-top:22px">
    <h2><?= e(txt('admin.users_title')) ?></h2>
    <p class="muted">Rollen und Rechte werden nicht in PHP entschieden. PHP versiegelt die Änderung, die Engine prüft <code>admin.users.manage</code> und aktualisiert den User-Attraktor.</p>
    <?php $permissionCatalog = $overview['permission_catalog'] ?? []; ?>
    <table class="table">
        <tr><th>User</th><th>Rolle</th><th>Rechte</th><th>Aktion</th></tr>
        <?php foreach (($overview['users'] ?? []) as $user): ?>
            <?php $userPermissions = is_array($user['permissions'] ?? null) ? $user['permissions'] : []; ?>
            <tr>
                <td>
                    <strong><?= e($user['username'] ?? '') ?></strong><br>
                    <span class="muted mono"><?= e($user['signature'] ?? '') ?></span>
                </td>
                <td>
                    <form method="post" data-direct-op="admin_update_user_rights">
                        <input type="hidden" name="signature" value="<?= e($user['signature'] ?? '') ?>">
                        <select name="role">
                            <?php foreach (['user' => 'User', 'moderator' => 'Moderator', 'admin' => 'Admin'] as $roleKey => $roleLabel): ?>
                                <option value="<?= e($roleKey) ?>" <?= mycelia_scalar_text($user['role'] ?? 'user') === $roleKey ? 'selected' : '' ?>><?= e($roleLabel) ?></option>
                            <?php endforeach; ?>
                        </select>
                </td>
                <td class="permissions-grid">
                    <?php foreach ($permissionCatalog as $perm): ?>
                        <?php $permKey = mycelia_scalar_text($perm['key'] ?? ''); ?>
                        <label class="checkline">
                            <input type="checkbox" name="permissions[]" value="<?= e($permKey) ?>" <?= in_array($permKey, $userPermissions, true) ? 'checked' : '' ?>>
                            <span><?= e($perm['label'] ?? $permKey) ?></span>
                        </label>
                    <?php endforeach; ?>
                </td>
                <td>
                        <button name="save_rights"><?= e(txt('admin.save_rights')) ?></button>
                    </form>
                </td>
            </tr>
        <?php endforeach; ?>
    </table>
</section>

<section class="panel" style="margin-top:22px">
    <h2><?= e(txt('admin.vram_title')) ?></h2>
    <p class="muted">
        Enterprise-Audit für Hardware-Residency. Wichtig: Plaintext-Probes dürfen für den harten Beweis
        nicht an PHP/Python gesendet werden. Die Engine liefert nur Manifest und PID; ein externer Scanner
        durchsucht den CPU-RAM des laufenden Prozesses und reicht anschließend einen JSON-Evidence-Report ein.
    </p>

    <div class="kpi">
        <form method="post"><button name="run_residency_manifest">Audit-Manifest erzeugen</button></form>
        <form method="post"><button name="run_restore_residency_audit">Snapshot-Restore-Pfad prüfen</button></form>
        <form method="post"><button name="run_native_gpu_report">Native-GPU-Opener prüfen</button></form>
        <form method="post"><button name="run_native_gpu_selftest">Native-GPU-Selftest</button></form>
        <form method="post"><button name="run_strict_certification">Strict-VRAM-Zertifizierung</button></form>
        <form method="post"><button name="run_vram_evidence_bundle">Konsole/UI synchronisieren</button></form>
    </div>

    <div class="panel heartbeat-card <?= !empty($heartbeatStatus['certified']) ? 'certified' : 'not-certified' ?>" style="margin-top:16px">
        <h3>Scheduled Heartbeat Audit</h3>
        <p>
            <strong>Aktueller Hardware-Residency-Status:</strong>
            <span class="<?= !empty($heartbeatStatus['certified']) ? 'ok' : 'warn' ?>">
                <?= e($heartbeatStatus['display']['value'] ?? 'UNBEKANNT') ?>
            </span>
        </p>
        <p class="muted">
            Automatisierter 24h-Audit: externes Random-Secret, CPU-RAM-Probe, signierter Evidence-Report,
            Engine-Verifikation und Dashboard-Status.
        </p>
        <?php if (!empty($heartbeatStatus['heartbeat_present'])): ?>
            <p class="muted">
                Alter: <?= e((string)round(floatval($heartbeatStatus['age_seconds'] ?? 0))) ?>s ·
                Max: <?= e((string)intval($heartbeatStatus['max_age_seconds'] ?? 0)) ?>s ·
                Signatur:
                <?= !empty($heartbeatStatus['latest']['signature']['signature_trusted']) ? 'gültig' : 'nicht vertrauenswürdig' ?>
            </p>
        <?php else: ?>
            <p class="warn">Noch kein Heartbeat-Audit vorhanden. Installiere die Scheduled Task oder starte <code>tools/run_heartbeat_audit.ps1</code>.</p>
        <?php endif; ?>
        <details>
            <summary>Heartbeat JSON anzeigen</summary>
            <pre><?= e(mycelia_admin_json($heartbeatStatus)) ?></pre>
        </details>
    </div>

    <?php if ($evidenceBundle): ?>
        <div class="codebox">
            <strong>Synchronisierte VRAM Evidence Bundle:</strong>
            <p>
                <strong>Strict 98%:</strong>
                <?= !empty($evidenceBundle['strict_98_security_supported']) ? 'SUPPORTED' : 'NICHT ZERTIFIZIERT' ?> ·
                <strong>Negative RAM-Probe:</strong>
                <?= !empty($evidenceBundle['negative_cpu_ram_probe']) ? 'ja' : 'nein' ?> ·
                <strong>Strict Gate:</strong>
                <?= !empty($evidenceBundle['strict_vram_certification_enabled']) ? 'aktiv' : 'deaktiviert' ?> ·
                <strong>Last Restore CPU:</strong>
                <?= !empty($evidenceBundle['last_restore_cpu_materialized']) ? 'ja' : 'nein' ?>
            </p>
            <?php if (empty($evidenceBundle['strict_vram_certification_enabled'])): ?>
                <p class="warn">
                    Strict Gate ist in diesem Engine-Prozess deaktiviert. Starte die Engine mit
                    <code>$env:MYCELIA_STRICT_VRAM_CERTIFICATION="1"</code>, bevor du zertifizierst.
                </p>
            <?php endif; ?>
            <pre><?= e(mycelia_admin_json($evidenceBundle)) ?></pre>
        </div>
    <?php endif; ?>

    <?php if ($manifest): ?>
        <div class="codebox">
            <strong>Externer Memory-Probe-Befehl:</strong>
            <pre><?= e($manifest['memory_probe_command_example'] ?? '') ?></pre>
            <pre><?= e(mycelia_admin_json($manifest)) ?></pre>
        </div>
    <?php endif; ?>

    <?php if ($nativeReport): ?>
        <div class="codebox">
            <strong>Native GPU Residency Bridge:</strong>
            <pre><?= e(mycelia_admin_json($nativeReport)) ?></pre>
        </div>
    <?php endif; ?>

    <?php if ($strictCert): ?>
        <div class="codebox">
            <strong>Strict VRAM Certification:</strong>
            <?= !empty($strictCert['strict_98_security_supported']) ? 'SUPPORTED' : 'NICHT ZERTIFIZIERT' ?>
            <pre><?= e(mycelia_admin_json($strictCert)) ?></pre>
        </div>
    <?php endif; ?>

    <form method="post" class="form-grid">
        <label>JSON-Report aus <code>tools/mycelia_memory_probe.py</code> einreichen</label>
        <textarea name="memory_probe_json" rows="8" placeholder="{ &quot;scanner_version&quot;: &quot;MYCELIA_CPU_RAM_PROBE_V1&quot;, ... }"></textarea>
        <button name="submit_memory_probe_report">External Memory Evidence einreichen</button>
    </form>

    <?php if ($probeSubmit): ?>
        <div class="codebox">
            <strong>Probe-Evidence:</strong>
            <pre><?= e(mycelia_admin_json($probeSubmit)) ?></pre>
        </div>
    <?php endif; ?>

    <details style="margin-top:16px">
        <summary>Legacy-Diagnose: Snapshot-/Graph-Scan mit Plaintext-Probes</summary>
        <p class="muted">Diese Diagnose ist nützlich für Snapshot-Vertraulichkeit, aber kein strenger CPU-RAM-Beweis, weil die Probe-Strings durch den Request selbst materialisiert werden.</p>
        <form method="post" class="form-grid" data-direct-op="vram_residency_audit">
            <label>Probe-Strings, eine pro Zeile oder kommagetrennt</label>
            <textarea name="probes" rows="4" placeholder="z.B. E-Mail, Nachname, geheime Testphrase"></textarea>
            <button name="run_vram_audit">Legacy-Audit ausführen</button>
        </form>
    </details>

    <?php if ($audit): ?>
        <div class="codebox">
            <strong>Status:</strong> <?= e($audit['status'] ?? 'error') ?> ·
            <strong>Strict 98%:</strong> <?= !empty($audit['strict_98_security_supported']) ? 'SUPPORTED' : 'NICHT BEWIESEN' ?> ·
            <strong>CPU-Risiko:</strong> <?= !empty($audit['cpu_cleartext_risk']) ? 'ja' : 'nein' ?>
            <pre><?= e(mycelia_admin_json($audit)) ?></pre>
        </div>
    <?php endif; ?>
</section>


<section class="panel" style="margin-top:22px">
    <h2>Enterprise v1.20: SMQL · Föderation · Provenance · Transport · Native Authenticity · Quantum Guard</h2>
    <form method="post" class="form-grid">
        <label>SMQL-Abfrage</label>
        <input name="smql_query" value="FIND * ASSOCIATED WITH &quot;High Security&quot; LIMIT 10">
        <button name="run_enterprise_v120_report">Enterprise-v1.20-Status prüfen</button>
    </form>
    <?php if ($enterpriseReport): ?>
        <div class="codebox">
            <strong>Enterprise v1.20 Report</strong>
            <pre><?= e(mycelia_admin_json($enterpriseReport)) ?></pre>
        </div>
    <?php endif; ?>
</section>

<section class="panel" style="margin-top:22px">
<h2><?= e(txt('admin.forum_title')) ?></h2>
<table class="table"><tr><th>Titel</th><th>Autor</th><th>Datum</th><th></th></tr>
<?php foreach (($overview['forum_threads'] ?? []) as $row): ?><tr><td><?= e($row['title']) ?></td><td><?= e($row['author_username']) ?></td><td><?= e(fmt_time($row['created_at'])) ?></td><td><form method="post" data-direct-op="delete_forum_thread"><input type="hidden" name="signature" value="<?= e($row['signature']) ?>"><button name="delete_thread" class="danger">Löschen</button></form></td></tr><?php endforeach; ?>
</table>
</section>

<section class="panel" style="margin-top:22px">
<h2><?= e(txt('admin.blogs_title')) ?></h2>
<table class="table"><tr><th>Titel</th><th>Owner</th><th>Posts</th><th></th></tr>
<?php foreach (($overview['blogs'] ?? []) as $row): ?><tr><td><?= e($row['title']) ?></td><td><?= e($row['owner_username']) ?></td><td><?= e($row['posts']) ?></td><td><form method="post" data-direct-op="delete_blog"><input type="hidden" name="signature" value="<?= e($row['signature']) ?>"><button name="delete_blog" class="danger">Löschen</button></form></td></tr><?php endforeach; ?>
</table>
</section>

<section class="panel" style="margin-top:22px">
<h2><?= e(txt('admin.blogposts_title')) ?></h2>
<table class="table"><tr><th>Titel</th><th>Autor</th><th>Status</th><th></th></tr>
<?php foreach (($overview['blog_posts'] ?? []) as $row): ?><tr><td><?= e($row['title']) ?></td><td><?= e($row['author_username']) ?></td><td><?= e($row['publish_status']) ?></td><td><form method="post" data-direct-op="delete_blog_post"><input type="hidden" name="signature" value="<?= e($row['signature']) ?>"><button name="delete_post" class="danger">Löschen</button></form></td></tr><?php endforeach; ?>
</table>
</section>

<section class="panel" style="margin-top:22px">
<h2><?= e(txt('admin.comments_title')) ?></h2>
<table class="table"><tr><th>Autor</th><th>Kommentar</th><th>Datum</th><th></th></tr>
<?php foreach (($overview['comments'] ?? []) as $row): ?><tr><td><?= e($row['author_username']) ?></td><td><?= e(ui_excerpt($row['body'] ?? '', 100)) ?></td><td><?= e(fmt_time($row['created_at'])) ?></td><td><form method="post" data-direct-op="delete_comment"><input type="hidden" name="signature" value="<?= e($row['signature']) ?>"><button name="delete_comment" class="danger">Löschen</button></form></td></tr><?php endforeach; ?>
</table>
</section>


<section class="panel" style="margin-top:22px">
<h2>Medienmoderation</h2>
<p class="muted">Bilder und sichere Embeds sind verschlüsselte Media-Attraktoren. Moderation ändert nur den Attraktorstatus, keine Webroot-Dateien.</p>
<table class="table"><tr><th>Titel</th><th>Typ</th><th>Ziel</th><th>Status</th><th>Größe</th><th>Aktion</th></tr>
<?php foreach (($overview['media'] ?? []) as $row): ?><tr>
<td><?= e($row['title'] ?? $row['filename'] ?? '') ?></td>
<td><?= e($row['media_kind'] ?? '') ?></td>
<td><?= e(mycelia_short_identifier(mycelia_scalar_text($row['target_signature'] ?? ''))) ?></td>
<td><?= e($row['moderation_status'] ?? '') ?></td>
<td><?= e($row['size_bytes'] ?? 0) ?> B</td>
<td>
<form method="post" data-direct-op="moderate_media" class="actions">
<input type="hidden" name="signature" value="<?= e($row['signature']) ?>">
<button name="action" value="quarantine" class="secondary">Quarantäne</button>
<button name="action" value="restore" class="secondary">Wiederherstellen</button>
<button name="action" value="delete" class="danger">Löschen</button>
</form>
</td>
</tr><?php endforeach; ?>
</table>
</section>

<?php layout_footer(); ?>
