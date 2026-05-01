<?php
require_once __DIR__ . '/bootstrap.php';
require_admin();

$lastRun = $_SESSION['_last_plugin_run'] ?? null;
unset($_SESSION['_last_plugin_run']);

if (!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])) {
    $op = strval($_POST['direct_op']);
    $response = call_mycelia_direct_ingest($op, strval($_POST['sealed_ingest']), direct_actor_context());
    if ($op === 'run_plugin') {
        $_SESSION['_last_plugin_run'] = $response;
    }
    $message = match ($op) {
        'admin_install_plugin' => 'Plugin-Attraktor wurde installiert.',
        'admin_set_plugin_state' => 'Plugin-Status wurde geändert.',
        'admin_delete_plugin' => 'Plugin-Attraktor wurde gelöscht.',
        'run_plugin' => 'Plugin wurde in der Capability-Sandbox ausgeführt.',
        default => 'Plugin-Aktion verarbeitet.',
    };
    flash(($response['status'] ?? '') === 'ok' ? $message : ($response['message'] ?? 'Plugin-Aktion fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('plugins.php');
}

$pluginsResponse = call_mycelia('list_plugins', []);
$plugins = ($pluginsResponse['status'] ?? '') === 'ok' ? ($pluginsResponse['plugins'] ?? []) : [];
$catalog = ($pluginsResponse['catalog'] ?? call_mycelia('plugin_catalog', []));
$enterprisePluginManifests = is_array($catalog['enterprise_plugins'] ?? null) ? $catalog['enterprise_plugins'] : [];
$manifestExample = json_encode($catalog['manifest_example'] ?? [
    'plugin_id' => 'anonymous_stats',
    'name' => 'Anonyme Statistiken',
    'version' => '1.0.0',
    'hooks' => ['admin.dashboard'],
    'capabilities' => ['stats.forum.count', 'stats.blog_post.count', 'stats.user.count'],
    'constraints' => ['max_records' => 10000, 'tension_threshold' => 0.72],
    'outputs' => [['key' => 'summary', 'type' => 'metric_cards']],
], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

layout_header(txt('plugins.title'));
?>
<section class="panel">
    <h1><?= e(txt('plugins.title')) ?></h1>
    <p class="muted"><?= e(txt('plugins.subtitle')) ?></p>
    <div class="kpi">
        <div><strong>Codeausführung:</strong> nein</div>
        <div><strong>I/O-Zugriff:</strong> nein</div>
        <div><strong>Rohdaten-Scan:</strong> nein</div>
        <div><strong>Modell:</strong> Capability-Sandbox</div>
    </div>
</section>

<?php if ($lastRun): ?>
<section class="panel" style="margin-top:22px">
    <h2>Letztes Plugin-Ergebnis</h2>
    <pre><?= e(json_encode($lastRun, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) ?></pre>
</section>
<?php endif; ?>

<section class="split" style="margin-top:22px">
    <div class="panel">
        <h2><?= e(txt('plugins.install_title')) ?></h2>
        <form method="post" data-direct-op="admin_install_plugin">
            <label><?= e(txt('plugins.manifest_label')) ?></label>
            <textarea name="manifest_json" rows="18"><?= e($manifestExample) ?></textarea>
            <button name="install_plugin"><?= e(txt('plugins.install_button')) ?></button>
        </form>
    </div>

    <div class="panel">
        <h2><?= e(txt('plugins.catalog_title')) ?></h2>
        <h3>Capabilities</h3>
        <ul>
            <?php foreach (($catalog['capabilities'] ?? []) as $cap): ?>
                <li><code><?= e($cap['key'] ?? '') ?></code> — <?= e($cap['label'] ?? '') ?></li>
            <?php endforeach; ?>
        </ul>
        <h3>Hooks</h3>
        <ul>
            <?php foreach (($catalog['hooks'] ?? []) as $hook): ?>
                <li><code><?= e($hook['key'] ?? '') ?></code> — <?= e($hook['label'] ?? '') ?></li>
            <?php endforeach; ?>
        </ul>
    </div>
</section>

<section class="panel" style="margin-top:22px">
    <h2>Enterprise Plugin-Vorlagen</h2>
    <p class="muted">Diese drei geprüften Manifeste sind für das Projekt vorbereitet. Installation bleibt deklarativ: kein PHP/Python-Code, keine I/O-Rechte, keine Rohdaten-Scans.</p>
    <div class="grid three">
        <?php foreach ($enterprisePluginManifests as $manifest): ?>
            <?php if (!is_array($manifest)) continue; ?>
            <div class="panel">
                <h3><?= e($manifest['name'] ?? '') ?></h3>
                <p class="muted"><?= e($manifest['description'] ?? '') ?></p>
                <p class="mono"><?= e($manifest['plugin_id'] ?? '') ?> · v<?= e($manifest['version'] ?? '') ?></p>
                <form method="post" data-direct-op="admin_install_plugin">
                    <input type="hidden" name="manifest_json" value="<?= e(json_encode($manifest, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) ?>">
                    <button>Installieren / aktualisieren</button>
                </form>
            </div>
        <?php endforeach; ?>
    </div>
</section>

<section class="panel" style="margin-top:22px">
    <h2><?= e(txt('plugins.installed_title')) ?></h2>
    <?php if (!$plugins): ?>
        <p class="muted">Noch keine Plugin-Attraktoren installiert.</p>
    <?php else: ?>
    <table class="table">
        <tr>
            <th>Plugin</th>
            <th>Capabilities</th>
            <th>Status</th>
            <th>Observer</th>
            <th>Aktionen</th>
        </tr>
        <?php foreach ($plugins as $plugin): ?>
            <tr>
                <td>
                    <strong><?= e($plugin['name'] ?? '') ?></strong><br>
                    <span class="muted mono"><?= e($plugin['plugin_id'] ?? '') ?> · v<?= e($plugin['version'] ?? '') ?></span><br>
                    <span class="muted"><?= e($plugin['description'] ?? '') ?></span>
                </td>
                <td>
                    <?php foreach (($plugin['capabilities'] ?? []) as $cap): ?>
                        <code><?= e($cap) ?></code><br>
                    <?php endforeach; ?>
                </td>
                <td><?= !empty($plugin['enabled']) ? 'aktiv' : e($plugin['status'] ?? 'disabled') ?></td>
                <td>
                    Tension: <?= e($plugin['tension'] ?? '0') ?><br>
                    <span class="muted">Last: <?= e($plugin['last_run_result'] ?? '-') ?></span>
                </td>
                <td>
                    <div class="actions">
                        <?php if (!empty($plugin['enabled'])): ?>
                            <form method="post" data-direct-op="run_plugin">
                                <input type="hidden" name="signature" value="<?= e($plugin['signature'] ?? '') ?>">
                                <button name="run_plugin"><?= e(txt('plugins.run_button')) ?></button>
                            </form>
                            <form method="post" data-direct-op="admin_set_plugin_state">
                                <input type="hidden" name="signature" value="<?= e($plugin['signature'] ?? '') ?>">
                                <input type="hidden" name="enabled" value="0">
                                <button name="disable_plugin" class="secondary"><?= e(txt('plugins.disable_button')) ?></button>
                            </form>
                        <?php else: ?>
                            <form method="post" data-direct-op="admin_set_plugin_state">
                                <input type="hidden" name="signature" value="<?= e($plugin['signature'] ?? '') ?>">
                                <input type="hidden" name="enabled" value="1">
                                <button name="enable_plugin"><?= e(txt('plugins.enable_button')) ?></button>
                            </form>
                        <?php endif; ?>
                        <form method="post" data-direct-op="admin_delete_plugin" onsubmit="return confirm('Plugin wirklich löschen?')">
                            <input type="hidden" name="signature" value="<?= e($plugin['signature'] ?? '') ?>">
                            <button name="delete_plugin" class="danger"><?= e(txt('plugins.delete_button')) ?></button>
                        </form>
                    </div>
                </td>
            </tr>
        <?php endforeach; ?>
    </table>
    <?php endif; ?>
</section>
<?php layout_footer(); ?>
