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
        <p><a class="button" href="forum.php"><?= e(txt('profile.open_forum')) ?></a></p>
        <p><a class="button" href="my_blog.php"><?= e(txt('profile.manage_blog')) ?></a></p>
        <p><a class="button secondary" href="privacy.php"><?= e(txt('profile.privacy_center')) ?></a></p>
        <?php if (is_admin()): ?><p><a class="button secondary" href="admin.php"><?= e(txt('profile.admin_console')) ?></a></p><?php endif; ?>
    </aside>
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
