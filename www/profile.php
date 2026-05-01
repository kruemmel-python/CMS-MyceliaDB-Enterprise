<?php
require_once __DIR__ . '/bootstrap.php';
require_login();
$signature = current_signature();
handle_direct_ingest('profile.php');

if (isset($_POST['update'])) {
    $profile = [
        'vorname' => $_POST['vorname'] ?? '',
        'nachname' => $_POST['nachname'] ?? '',
        'strasse' => $_POST['strasse'] ?? '',
        'hnr' => $_POST['hnr'] ?? '',
        'plz' => $_POST['plz'] ?? '',
        'ort' => $_POST['ort'] ?? '',
        'email' => $_POST['email'] ?? '',
        'role' => current_role()
    ];
    $response = call_mycelia('update_profile', ['signature' => $signature, 'profile' => $profile]);
    flash(($response['status'] ?? '') === 'ok' ? 'Profil im Myzel aktualisiert.' : ($response['message'] ?? 'Update fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('profile.php');
}

$response = require_mycelia_ok(call_mycelia('get_profile', ['signature' => $signature]));
$data = $response['profile'] ?? [];
$node = $response['node'] ?? [];
$e2eeInbox = call_mycelia('e2ee_inbox', engine_session_context());
$e2eeOutbox = call_mycelia('e2ee_outbox', engine_session_context());
$myE2eeKeys = call_mycelia('e2ee_public_key_lookup', ['owner_signature' => $signature] + engine_session_context());
$e2eeDirectory = call_mycelia('e2ee_recipient_directory', engine_session_context());
$enterprisePlugins = call_mycelia('enterprise_plugin_dashboard', engine_session_context());
$enterprisePluginData = is_array($enterprisePlugins['plugins'] ?? null) ? $enterprisePlugins['plugins'] : [];
$funPlugins = call_mycelia('fun_plugin_dashboard', engine_session_context());
$funPluginData = is_array($funPlugins['plugins'] ?? null) ? $funPlugins['plugins'] : [];
$inboxMessages = is_array($e2eeInbox['messages'] ?? null) ? $e2eeInbox['messages'] : [];
$outboxMessages = is_array($e2eeOutbox['messages'] ?? null) ? $e2eeOutbox['messages'] : [];
$ownPublicJwk = e2ee_latest_own_public_key_jwk($myE2eeKeys);
$recipients = is_array($e2eeDirectory['recipients'] ?? null) ? $e2eeDirectory['recipients'] : [];
$messageableOthers = [];
$selfEntry = null;
foreach ($recipients as $recipient) {
    if (!is_array($recipient)) {
        continue;
    }
    if (!empty($recipient['is_self']) || strval($recipient['user_signature'] ?? '') === $signature) {
        $selfEntry = $recipient;
        continue;
    }
    if (!empty($recipient['messageable']) && is_array($recipient['latest_key'] ?? null)) {
        $messageableOthers[] = $recipient;
    }
}
function profile_e2ee_recipient_option_label(array $recipient): string {
    $username = trim(strval($recipient['username'] ?? 'Unbekannt'));
    $sig = strval($recipient['user_signature'] ?? '');
    $key = is_array($recipient['latest_key'] ?? null) ? $recipient['latest_key'] : [];
    $keySig = strval($key['signature'] ?? $key['key_signature'] ?? '');
    $label = $username !== '' ? $username : 'Unbekannt';
    return $label . ' · User ' . substr($sig, 0, 10) . '… · Key ' . substr($keySig, 0, 10) . '…';
}
layout_header(txt('profile.title'));
?>
<section class="split">
    <div class="panel">
        <h1><?= e(txt('profile.welcome')) ?>, <?= e(current_username()) ?></h1>
        <p class="muted mono">SIGNATURE <?= e($signature) ?> · STABILITY <?= e($node['stability'] ?? 'n/a') ?> · STORAGE encrypted-attractor / no SQL</p>
        <form method="post" data-direct-op="update_profile">
            <input type="hidden" name="role" value="<?= e(current_role()) ?>">
            <label>Vorname</label><input name="vorname" value="<?= e($data['vorname'] ?? '') ?>">
            <label>Nachname</label><input name="nachname" value="<?= e($data['nachname'] ?? '') ?>">
            <label>Straße</label><input name="strasse" value="<?= e($data['strasse'] ?? '') ?>">
            <div class="grid two"><div><label>Nr.</label><input name="hnr" value="<?= e($data['hnr'] ?? '') ?>"></div><div><label>PLZ</label><input name="plz" value="<?= e($data['plz'] ?? '') ?>"></div></div>
            <label>Ort</label><input name="ort" value="<?= e($data['ort'] ?? '') ?>">
            <label>E-Mail</label><input name="email" value="<?= e($data['email'] ?? '') ?>">
            <button name="update"><?= e(txt('profile.update_button')) ?></button>
        </form>
    </div>
    <aside class="panel">
        <h2><?= e(txt('profile.actions')) ?></h2>
        <p><a class="button" href="#messages">Nachrichten Inbox/Outbox</a></p>
        <p><a class="button secondary" href="#enterprise-plugins">Enterprise Plugins</a></p><p><a class="button secondary" href="#fun-plugins">Spaß-Plugins</a></p>
        <p><a class="button" href="forum.php"><?= e(txt('profile.open_forum')) ?></a></p>
        <p><a class="button" href="my_blog.php"><?= e(txt('profile.manage_blog')) ?></a></p>
        <p><a class="button secondary" href="privacy.php"><?= e(txt('profile.privacy_center')) ?></a></p>
        <?php if (is_admin()): ?><p><a class="button secondary" href="admin.php"><?= e(txt('profile.admin_console')) ?></a></p><?php endif; ?>
    </aside>
</section>


<section class="card" id="enterprise-plugins">
    <h2>Enterprise Plugins</h2>
    <p class="muted">Drei sichere Plugin-Widgets laufen als deklarative Mycelia-Attraktoren: Digest, Privacy Guardian und Content Trust Lens. Sie liefern nur erlaubte Aggregate und keine E2EE-Klartexte.</p>
    <?php
      $digest = is_array($enterprisePluginData['mycelia_digest'] ?? null) ? $enterprisePluginData['mycelia_digest'] : [];
      $privacy = is_array($enterprisePluginData['privacy_guardian'] ?? null) ? $enterprisePluginData['privacy_guardian'] : [];
      $trust = is_array($enterprisePluginData['content_trust_lens'] ?? null) ? $enterprisePluginData['content_trust_lens'] : [];
      $digestSummary = is_array($digest['summary'] ?? null) ? $digest['summary'] : [];
      $privacyInventory = is_array($privacy['inventory'] ?? null) ? $privacy['inventory'] : [];
      $trustSummary = is_array($trust['summary'] ?? null) ? $trust['summary'] : [];
    ?>
    <div class="grid three">
        <div class="panel">
            <h3>Mycelia Digest</h3>
            <p class="muted">Persönliche Aktivitätszentrale ohne private Rohdaten.</p>
            <ul>
                <li>Inbox: <?= e((string)($digest['unread_e2ee_count'] ?? 0)) ?></li>
                <li>Outbox: <?= e((string)($digest['outbox_count'] ?? 0)) ?></li>
                <li>Kommentare auf eigene Inhalte: <?= e((string)($digestSummary['comments_on_own_content'] ?? 0)) ?></li>
                <li>Reaktionen auf eigene Inhalte: <?= e((string)($digestSummary['reactions_on_own_content'] ?? 0)) ?></li>
            </ul>
            <?php foreach (($digest['notifications'] ?? []) as $note): if (!is_array($note)) continue; ?>
                <p class="ok"><?= e($note['label'] ?? '') ?>: <?= e((string)($note['count'] ?? 0)) ?></p>
            <?php endforeach; ?>
        </div>
        <div class="panel">
            <h3>Privacy Guardian</h3>
            <p class="muted">Daten-Souveränität, Export- und Löschhinweise.</p>
            <ul>
                <li>Öffentliche Inhalte: <?= e((string)($privacy['public_content_count'] ?? 0)) ?></li>
                <li>Medien: <?= e((string)($privacy['media_count'] ?? 0)) ?></li>
                <li>E2EE-Keys: <?= e((string)($privacyInventory['e2ee_public_keys'] ?? 0)) ?></li>
                <li>Ephemere Inhalte: <?= e((string)($privacyInventory['ephemeral_items'] ?? 0)) ?></li>
            </ul>
            <p><a class="button secondary" href="privacy.php">Datenschutz-Center öffnen</a></p>
        </div>
        <div class="panel">
            <h3>Content Trust & Safety Lens</h3>
            <p class="muted">Öffentliche Diskussionssignale ohne private Klartexte.</p>
            <ul>
                <li>Bewertete Ziele: <?= e((string)($trustSummary['targets_scored'] ?? 0)) ?></li>
                <li>Ø Trust: <?= e((string)($trustSummary['average_trust'] ?? 'n/a')) ?></li>
                <li>Prüfhinweise: <?= e((string)($trustSummary['attention_needed'] ?? 0)) ?></li>
            </ul>
            <?php foreach (($trust['cards'] ?? []) as $card): if (!is_array($card)) continue; ?>
                <p class="muted mono"><?= e(substr(strval($card['target_signature'] ?? ''), 0, 10)) ?>… · <?= e($card['label'] ?? '') ?> · <?= e((string)($card['trust_score'] ?? '')) ?></p>
            <?php endforeach; ?>
        </div>
    </div>
</section>


<section class="card" id="fun-plugins">
    <h2>Spaß-Plugins</h2>
    <p class="muted">Zehn Community-Plugins für Badges, Quests, Pulse, Sticker-Reactions, Discovery, Creator Cards, Polls und Time Capsules. Alle Widgets nutzen nur erlaubte Aggregate oder eigene Daten.</p>
    <?php
      $ach = is_array($funPluginData['mycelia_achievements'] ?? null) ? $funPluginData['mycelia_achievements'] : [];
      $pulse = is_array($funPluginData['daily_pulse'] ?? null) ? $funPluginData['daily_pulse'] : [];
      $quests = is_array($funPluginData['mycelia_quests'] ?? null) ? $funPluginData['mycelia_quests'] : [];
      $stickers = is_array($funPluginData['reaction_stickers'] ?? null) ? $funPluginData['reaction_stickers'] : [];
      $themes = is_array($funPluginData['blog_mood_themes'] ?? null) ? $funPluginData['blog_mood_themes'] : [];
      $constellation = is_array($funPluginData['community_constellation'] ?? null) ? $funPluginData['community_constellation'] : [];
      $discovery = is_array($funPluginData['random_discovery'] ?? null) ? $funPluginData['random_discovery'] : [];
      $creators = is_array($funPluginData['creator_cards'] ?? null) ? $funPluginData['creator_cards'] : [];
      $polls = is_array($funPluginData['polls'] ?? null) ? $funPluginData['polls'] : [];
      $capsules = is_array($funPluginData['time_capsules'] ?? null) ? $funPluginData['time_capsules'] : [];
    ?>
    <div class="grid three">
        <div class="panel"><h3>Achievements</h3><p class="ok"><?= e((string)($ach['earned_count'] ?? 0)) ?> Badges erreicht</p><?php foreach (($ach['badges'] ?? []) as $b): if (!is_array($b)) continue; ?><span class="badge <?= !empty($b['earned']) ? 'ok' : 'muted' ?>"><?= e($b['label'] ?? '') ?></span> <?php endforeach; ?></div>
        <div class="panel"><h3>Daily Pulse</h3><?php $ps = is_array($pulse['summary'] ?? null) ? $pulse['summary'] : []; ?><p>Stimmung: <strong><?= e($ps['community_mood'] ?? 'ruhig') ?></strong></p><p class="muted">Neu: <?= e((string)($ps['new_public_content'] ?? 0)) ?> · Kommentare: <?= e((string)($ps['comments_today'] ?? 0)) ?> · Reaktionen: <?= e((string)($ps['reactions_today'] ?? 0)) ?></p></div>
        <div class="panel"><h3>Quests</h3><p class="muted">Offen: <?= e((string)($quests['open_count'] ?? 0)) ?></p><?php foreach (($quests['active_quests'] ?? []) as $q): if (!is_array($q)) continue; ?><p><?= !empty($q['complete']) ? '✅' : '⬜' ?> <?= e($q['label'] ?? '') ?></p><?php endforeach; ?></div>
        <div class="panel"><h3>Reaction Stickers</h3><?php foreach (($stickers['allowed_reactions'] ?? []) as $r): if (!is_array($r)) continue; ?><span class="badge"><?= e($r['label'] ?? '') ?> <?= e((string)($r['count'] ?? 0)) ?></span> <?php endforeach; ?></div>
        <div class="panel"><h3>Blog Mood Themes</h3><?php foreach (($themes['themes'] ?? []) as $t): if (!is_array($t)) continue; ?><span class="badge"><?= e($t['label'] ?? '') ?> <?= e((string)($t['count'] ?? 0)) ?></span> <?php endforeach; ?></div>
        <div class="panel"><h3>Community Constellation</h3><?php foreach (($constellation['nodes'] ?? []) as $n): if (!is_array($n)) continue; ?><p class="muted"><?= e($n['label'] ?? '') ?>: <?= e((string)($n['weight'] ?? 0)) ?></p><?php endforeach; ?></div>
        <div class="panel"><h3>Sporenflug Discovery</h3><?php foreach (($discovery['items'] ?? []) as $it): if (!is_array($it)) continue; ?><p><a href="<?= e(($it['kind'] ?? '') === 'blog' ? 'blog.php?id=' . ($it['signature'] ?? '') : (($it['kind'] ?? '') === 'forum_thread' ? 'thread.php?id=' . ($it['signature'] ?? '') : 'blogs.php')) ?>"><?= e($it['title'] ?? 'Entdecken') ?></a> <span class="muted"><?= e($it['trust_label'] ?? '') ?></span></p><?php endforeach; ?></div>
        <div class="panel"><h3>Creator Cards</h3><?php foreach (($creators['cards'] ?? []) as $c): if (!is_array($c)) continue; ?><p><strong><?= e($c['username'] ?? '') ?></strong> · Blogs <?= e((string)($c['blogs'] ?? 0)) ?> · Threads <?= e((string)($c['threads'] ?? 0)) ?> · Badges <?= e((string)($c['badges'] ?? 0)) ?></p><?php endforeach; ?></div>
        <div class="panel"><h3>Polls</h3><p class="muted">Offene Umfragen: <?= e((string)($polls['open_count'] ?? 0)) ?></p><p><a class="button secondary" href="fun.php#polls">Umfragen öffnen</a></p></div>
        <div class="panel"><h3>Time Capsules</h3><p class="muted">Bereit: <?= e((string)($capsules['ready_count'] ?? 0)) ?> · Wartend: <?= e((string)($capsules['waiting_count'] ?? 0)) ?></p><p><a class="button secondary" href="fun.php#time-capsules">Zeitkapseln öffnen</a></p></div>
    </div>
</section>

<section class="card" id="messages">
    <h2>Nachrichten</h2>
    <p class="muted">Posteingang, Postausgang, Antworten und Löschen direkt im Profil. Klartext wird ausschließlich im Browser entschlüsselt.</p>
    <div class="actions">
        <a class="button secondary" href="#e2ee-compose">Neue Nachricht</a>
        <a class="button secondary" href="#e2ee-inbox">Inbox (<?= e((string)count($inboxMessages)) ?>)</a>
        <a class="button secondary" href="#e2ee-outbox">Outbox (<?= e((string)count($outboxMessages)) ?>)</a>
        <a class="button secondary" href="e2ee.php">E2EE-Schlüssel verwalten</a>
    </div>
</section>

<section class="card" id="e2ee-compose">
    <h2>Nachricht schreiben</h2>
    <?php if (!$ownPublicJwk): ?>
        <p class="warn">Du hast noch keinen E2EE-Public-Key registriert. Öffne „E2EE-Schlüssel verwalten“, erzeuge einen Schlüssel und registriere ihn. Danach ist auch deine Outbox lesbar.</p>
    <?php endif; ?>
    <?php if (!$messageableOthers): ?>
        <p class="warn">Noch kein anderer Nutzer hat einen E2EE-Public-Key registriert. Der Empfänger muss sich einloggen und einmal einen E2EE-Schlüssel registrieren.</p>
    <?php else: ?>
        <p class="ok"><?= e((string)count($messageableOthers)) ?> andere E2EE-Empfänger verfügbar. Wähle einfach den Nutzer aus.</p>
    <?php endif; ?>

    <form method="post" data-direct-op="e2ee_send_message" id="e2ee-send-form">
        <label>Empfänger</label>
        <select id="e2ee-recipient-select" required>
            <option value="">Empfänger wählen …</option>
            <?php foreach ($messageableOthers as $recipient): ?>
                <?php
                  $key = is_array($recipient['latest_key'] ?? null) ? $recipient['latest_key'] : [];
                  $userSig = strval($recipient['user_signature'] ?? '');
                  $username = strval($recipient['username'] ?? '');
                  $keySig = strval($key['signature'] ?? $key['key_signature'] ?? '');
                  $hash = strval($key['public_key_hash'] ?? '');
                  $jwkText = e2ee_safe_jwk_text($key['public_key_jwk'] ?? '');
                ?>
                <option
                  value="<?= e($userSig) ?>"
                  data-recipient-signature="<?= e($userSig) ?>"
                  data-recipient-username="<?= e($username) ?>"
                  data-recipient-key-signature="<?= e($keySig) ?>"
                  data-public-key-jwk="<?= e($jwkText) ?>"
                  data-public-key-hash="<?= e($hash) ?>"
                ><?= e(profile_e2ee_recipient_option_label($recipient)) ?></option>
            <?php endforeach; ?>
            <?php if (!$messageableOthers && is_array($selfEntry) && !empty($selfEntry['messageable']) && is_array($selfEntry['latest_key'] ?? null)): ?>
                <?php
                  $key = $selfEntry['latest_key'];
                  $userSig = strval($selfEntry['user_signature'] ?? '');
                  $username = strval($selfEntry['username'] ?? current_username());
                  $keySig = strval($key['signature'] ?? $key['key_signature'] ?? '');
                  $hash = strval($key['public_key_hash'] ?? '');
                  $jwkText = e2ee_safe_jwk_text($key['public_key_jwk'] ?? '');
                ?>
                <option
                  value="<?= e($userSig) ?>"
                  data-recipient-signature="<?= e($userSig) ?>"
                  data-recipient-username="<?= e($username) ?>"
                  data-recipient-key-signature="<?= e($keySig) ?>"
                  data-public-key-jwk="<?= e($jwkText) ?>"
                  data-public-key-hash="<?= e($hash) ?>"
                  data-allow-self="1"
                >Selbsttest an <?= e(current_username()) ?> · Key <?= e(substr($keySig, 0, 10)) ?>…</option>
            <?php endif; ?>
        </select>

        <input type="hidden" name="recipient_signature" id="recipient_signature" required>
        <input type="hidden" name="recipient_key_signature" id="recipient_key_signature" required>
        <input type="hidden" name="recipient_username" id="recipient_username">
        <textarea id="recipient_public_key_jwk" rows="4" readonly hidden required></textarea>

        <label>Nachricht</label>
        <textarea id="e2ee_plaintext" rows="6" required placeholder="Nachricht eingeben …"></textarea>

        <input type="hidden" name="ciphertext_b64" id="e2ee_ciphertext_b64">
        <input type="hidden" name="nonce_b64" id="e2ee_nonce_b64">
        <input type="hidden" name="eph_public_jwk" id="e2ee_eph_public_jwk">
        <input type="hidden" name="recipient_key_hash" id="e2ee_recipient_key_hash">

        <input type="hidden" id="sender_public_key_jwk" value="<?= e($ownPublicJwk) ?>">
        <input type="hidden" name="sender_ciphertext_b64" id="e2ee_sender_ciphertext_b64">
        <input type="hidden" name="sender_nonce_b64" id="e2ee_sender_nonce_b64">
        <input type="hidden" name="sender_eph_public_jwk" id="e2ee_sender_eph_public_jwk">
        <input type="hidden" name="sender_key_hash" id="e2ee_sender_key_hash">

        <input type="hidden" name="aad" value="mycelia-e2ee-v1">
        <input type="hidden" name="allow_self_message" id="e2ee_allow_self_message" value="0">

        <button>Browserseitig verschlüsseln & senden</button>
    </form>
</section>

<section class="split">
    <div class="panel" id="e2ee-inbox">
        <h2>Nachrichten Inbox</h2>
        <p class="muted">Eingehende E2EE-Nachrichten. Klicke „Lesen“, um lokal zu entschlüsseln. „Antworten“ füllt die Schreibmaske oben automatisch.</p>
        <?php e2ee_render_mailbox($inboxMessages, 'inbox'); ?>
    </div>
    <div class="panel" id="e2ee-outbox">
        <h2>Nachrichten Outbox</h2>
        <p class="muted">Gesendete E2EE-Nachrichten. Neue Nachrichten enthalten eine senderseitige Browser-Kopie für dein eigenes Lesen.</p>
        <?php e2ee_render_mailbox($outboxMessages, 'outbox'); ?>
    </div>
</section>

<?php layout_footer(); ?>
