<?php
require_once __DIR__ . '/bootstrap.php';
require_login();
handle_direct_ingest('fun.php');

$dashboard = call_mycelia('fun_plugin_dashboard', engine_session_context());
$plugins = is_array($dashboard['plugins'] ?? null) ? $dashboard['plugins'] : [];
$enabledFunPlugins = is_array($dashboard['enabled_plugin_ids'] ?? null) ? array_map('strval', $dashboard['enabled_plugin_ids']) : [];
$pollsEnabled = in_array('polls', $enabledFunPlugins, true);
$timeCapsulesEnabled = in_array('time_capsules', $enabledFunPlugins, true);
$pollsResponse = $pollsEnabled ? call_mycelia('list_polls', engine_session_context()) : ['polls' => []];
$polls = is_array($pollsResponse['polls'] ?? null) ? $pollsResponse['polls'] : [];
$capsulesResponse = $timeCapsulesEnabled ? call_mycelia('list_time_capsules', engine_session_context()) : ['capsules' => []];
$capsules = is_array($capsulesResponse['capsules'] ?? null) ? $capsulesResponse['capsules'] : [];

layout_header('Spaß-Plugins');
?>
<section class="card">
    <h1>Mycelia Spaß-Plugins</h1>
    <p class="muted">Achievements, Daily Pulse, Quests, Reaction Stickers, Blog Themes, Community Constellation, Sporenflug Discovery, Creator Cards, Polls und Time Capsules.</p>
</section>

<?php if (!$plugins): ?>
<section class="card">
    <h2>Keine Spaß-Plugins aktiv</h2>
    <p class="muted">Die verfügbaren Plugin-Vorlagen sind erst sichtbar und nutzbar, nachdem ein Admin sie im Plugin-Bereich installiert und aktiviert hat.</p>
</section>
<?php endif; ?>

<section class="grid three">
<?php foreach ($plugins as $id => $plugin): if (!is_array($plugin)) continue; ?>
    <article class="panel">
        <h2><?= e(str_replace('_', ' ', (string)$id)) ?></h2>
        <p class="muted mono"><?= e($plugin['status'] ?? 'ok') ?> · raw_records_returned=<?= e((string)($plugin['raw_records_returned'] ?? 0)) ?></p>
        <?php if ($id === 'mycelia_achievements'): ?>
            <p>Badges erreicht: <?= e((string)($plugin['earned_count'] ?? 0)) ?></p>
            <?php foreach (($plugin['badges'] ?? []) as $badge): if (!is_array($badge)) continue; ?>
                <span class="badge <?= !empty($badge['earned']) ? 'ok' : 'muted' ?>"><?= e($badge['label'] ?? '') ?></span>
            <?php endforeach; ?>
        <?php elseif ($id === 'daily_pulse'): $s = is_array($plugin['summary'] ?? null) ? $plugin['summary'] : []; ?>
            <p><strong><?= e($s['community_mood'] ?? 'ruhig') ?></strong></p>
            <p class="muted">Neu <?= e((string)($s['new_public_content'] ?? 0)) ?> · Kommentare <?= e((string)($s['comments_today'] ?? 0)) ?> · Reaktionen <?= e((string)($s['reactions_today'] ?? 0)) ?></p>
        <?php elseif ($id === 'reaction_stickers'): ?>
            <?php foreach (($plugin['allowed_reactions'] ?? []) as $r): if (!is_array($r)) continue; ?><span class="badge"><?= e($r['label'] ?? '') ?> <?= e((string)($r['count'] ?? 0)) ?></span><?php endforeach; ?>
        <?php elseif ($id === 'community_constellation'): ?>
            <?php foreach (($plugin['nodes'] ?? []) as $n): if (!is_array($n)) continue; ?><p><?= e($n['label'] ?? '') ?>: <?= e((string)($n['weight'] ?? 0)) ?></p><?php endforeach; ?>
        <?php elseif ($id === 'random_discovery'): ?>
            <?php foreach (($plugin['items'] ?? []) as $it): if (!is_array($it)) continue; ?><p><?= e($it['title'] ?? 'Entdecken') ?> <span class="muted"><?= e($it['trust_label'] ?? '') ?></span></p><?php endforeach; ?>
        <?php elseif ($id === 'creator_cards'): ?>
            <?php foreach (($plugin['cards'] ?? []) as $card): if (!is_array($card)) continue; ?><p><strong><?= e($card['username'] ?? '') ?></strong> · Blogs <?= e((string)($card['blogs'] ?? 0)) ?> · Threads <?= e((string)($card['threads'] ?? 0)) ?></p><?php endforeach; ?>
        <?php else: ?>
            <pre><?= e(json_encode($plugin, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) ?></pre>
        <?php endif; ?>
    </article>
<?php endforeach; ?>
</section>

<section class="split">
    <div class="panel" id="polls">
        <h2>Polls / Abstimmungen</h2>
        <?php if (!$pollsEnabled): ?>
            <p class="muted">Polls sind erst verfügbar, wenn das Plugin <strong>Polls / Abstimmungen</strong> installiert und aktiviert wurde.</p>
        <?php else: ?>
        <form method="post" data-direct-op="create_poll">
            <label>Frage</label><input name="question" required maxlength="300">
            <label>Option 1</label><input name="option_1" required maxlength="140">
            <label>Option 2</label><input name="option_2" required maxlength="140">
            <label>Option 3</label><input name="option_3" maxlength="140">
            <label>Option 4</label><input name="option_4" maxlength="140">
            <button>Umfrage erstellen</button>
        </form>
        <?php foreach ($polls as $poll): if (!is_array($poll)) continue; ?>
            <article class="card">
                <h3><?= e($poll['question'] ?? '') ?></h3>
                <?php foreach (($poll['options'] ?? []) as $opt): if (!is_array($opt)) continue; ?>
                    <form method="post" data-direct-op="vote_poll" class="inline">
                        <input type="hidden" name="poll_signature" value="<?= e($poll['signature'] ?? '') ?>">
                        <input type="hidden" name="option_id" value="<?= e($opt['id'] ?? '') ?>">
                        <button><?= e($opt['label'] ?? '') ?> · <?= e((string)($opt['votes'] ?? 0)) ?></button>
                    </form>
                <?php endforeach; ?>
            </article>
        <?php endforeach; ?>
        <?php endif; ?>
    </div>
    <div class="panel" id="time-capsules">
        <h2>Time Capsules</h2>
        <?php if (!$timeCapsulesEnabled): ?>
            <p class="muted">Time Capsules sind erst verfügbar, wenn das Plugin <strong>Time Capsules</strong> installiert und aktiviert wurde.</p>
        <?php else: ?>
        <form method="post" data-direct-op="create_time_capsule">
            <label>Titel</label><input name="title" required maxlength="180">
            <label>Inhalt</label><textarea name="body" required rows="5"></textarea>
            <label>Öffnen ab</label><input name="reveal_at" placeholder="2026-05-01T12:00:00">
            <label>Sichtbarkeit</label><select name="visibility"><option value="private">privat</option><option value="public">öffentlich nach Reveal</option></select>
            <button>Zeitkapsel speichern</button>
        </form>
        <?php foreach ($capsules as $cap): if (!is_array($cap)) continue; ?>
            <article class="card">
                <h3><?= e($cap['title'] ?? '') ?></h3>
                <p class="muted">Reveal: <?= e(fmt_time($cap['reveal_at'] ?? null)) ?> · <?= !empty($cap['is_revealed']) ? 'offen' : 'wartet' ?></p>
                <?php if (!empty($cap['is_revealed']) && is_array($cap['content'] ?? null)): ?><p><?= e($cap['content']['body'] ?? '') ?></p><?php endif; ?>
            </article>
        <?php endforeach; ?>
        <?php endif; ?>
    </div>
</section>
<?php layout_footer(); ?>
