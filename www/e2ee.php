<?php
require_once __DIR__ . '/bootstrap.php';
require_login();

handle_direct_ingest('e2ee.php');

$myKeys = call_mycelia(
    'e2ee_public_key_lookup',
    ['owner_signature' => current_signature()] + engine_session_context()
);
$directory = call_mycelia(
    'e2ee_recipient_directory',
    engine_session_context()
);
$inbox = call_mycelia('e2ee_inbox', engine_session_context());
$outbox = call_mycelia('e2ee_outbox', engine_session_context());

layout_header('E2EE Direktnachrichten');

$recipients = is_array($directory['recipients'] ?? null) ? $directory['recipients'] : [];
$ownSig = current_signature();
$messageableOthers = [];
$selfEntry = null;
foreach ($recipients as $recipient) {
    if (!is_array($recipient)) {
        continue;
    }
    if (!empty($recipient['is_self']) || strval($recipient['user_signature'] ?? '') === $ownSig) {
        $selfEntry = $recipient;
        continue;
    }
    if (!empty($recipient['messageable']) && is_array($recipient['latest_key'] ?? null)) {
        $messageableOthers[] = $recipient;
    }
}

function e2ee_recipient_option_label(array $recipient): string {
    $username = trim(strval($recipient['username'] ?? 'Unbekannt'));
    $sig = strval($recipient['user_signature'] ?? '');
    $key = is_array($recipient['latest_key'] ?? null) ? $recipient['latest_key'] : [];
    $keySig = strval($key['signature'] ?? $key['key_signature'] ?? '');
    $label = $username !== '' ? $username : 'Unbekannt';
    return $label . ' · User ' . substr($sig, 0, 10) . '… · Key ' . substr($keySig, 0, 10) . '…';
}

$ownPublicJwk = e2ee_latest_own_public_key_jwk($myKeys);
$inboxMessages = is_array($inbox['messages'] ?? null) ? $inbox['messages'] : [];
$outboxMessages = is_array($outbox['messages'] ?? null) ? $outbox['messages'] : [];
?>
<section class="card">
  <h1>E2EE Direktnachrichten</h1>
  <p>Die Engine speichert nur blind verschlüsselte Blobs. Entschlüsselung findet im Browser des Empfängers statt.</p>
  <p class="muted">Wichtig: Damit du einem anderen Nutzer schreiben kannst, muss dieser Nutzer einmal auf dieser Seite einen E2EE-Schlüssel erzeugen und seinen Public Key registrieren. Ohne Public Key gibt es absichtlich keinen Klartext-Fallback.</p>
  <button type="button" id="e2ee-generate">E2EE-Schlüssel im Browser erzeugen</button>
  <form method="post" data-direct-op="e2ee_register_public_key" id="e2ee-key-form">
    <input type="hidden" name="public_key_jwk" id="e2ee-public-key">
    <input type="hidden" name="encrypted_private_key" id="e2ee-private-key">
    <button>Public Key registrieren</button>
  </form>
</section>

<section class="card" id="e2ee-compose">
  <h2>Nachricht senden</h2>
  <?php if (!$ownPublicJwk): ?>
    <p class="warn">Du hast noch keinen registrierten E2EE-Public-Key. Erzeuge zuerst einen Schlüssel und registriere ihn. Danach kann deine Outbox später auch eigene gesendete Nachrichten entschlüsseln.</p>
  <?php endif; ?>
  <?php if (!$messageableOthers): ?>
    <p class="warn">Noch kein anderer Nutzer hat einen E2EE-Public-Key registriert. Deshalb ist aktuell nur ein Selbsttest möglich. Melde dich mit dem zweiten Nutzer an, öffne E2EE und registriere dort einen Public Key.</p>
  <?php else: ?>
    <p class="ok">Es sind <?= e((string)count($messageableOthers)) ?> andere E2EE-Empfänger verfügbar. Du musst keine Signaturen kopieren.</p>
  <?php endif; ?>

  <form method="post" data-direct-op="e2ee_send_message" id="e2ee-send-form">
    <label>Empfänger auswählen</label>
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
        ><?= e(e2ee_recipient_option_label($recipient)) ?></option>
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
    <textarea id="e2ee_plaintext" rows="6" required></textarea>

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
  <div class="panel">
    <h2>Inbox</h2>
    <p class="muted">Eingehende Nachrichten. Klicke „Lesen“, um lokal im Browser zu entschlüsseln.</p>
    <?php e2ee_render_mailbox($inboxMessages, 'inbox'); ?>
  </div>
  <div class="panel">
    <h2>Outbox</h2>
    <p class="muted">Gesendete Nachrichten. Neue Nachrichten werden zusätzlich an deinen eigenen Public Key verschlüsselt, damit du sie später lesen kannst.</p>
    <?php e2ee_render_mailbox($outboxMessages, 'outbox'); ?>
  </div>
</section>

<section class="card">
  <h2>E2EE-Empfänger-Verzeichnis</h2>
  <p class="muted">Dieses Verzeichnis enthält nur Username, User-Signatur und öffentliche E2EE-Schlüssel. Private Schlüssel, Nachrichteninhalte und Profile werden nicht ausgegeben.</p>
  <table>
    <thead>
      <tr>
        <th>Nutzer</th>
        <th>Status</th>
        <th>User-Signatur</th>
        <th>Key</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($recipients as $recipient): ?>
        <?php
          if (!is_array($recipient)) { continue; }
          $key = is_array($recipient['latest_key'] ?? null) ? $recipient['latest_key'] : [];
          $hasKey = !empty($recipient['messageable']) && $key;
        ?>
        <tr>
          <td><?= e(strval($recipient['username'] ?? 'Unbekannt')) ?><?= !empty($recipient['is_self']) ? ' (du)' : '' ?></td>
          <td><?= $hasKey ? '<span class="ok">bereit</span>' : '<span class="warn">kein E2EE-Key</span>' ?></td>
          <td><code><?= e(substr(strval($recipient['user_signature'] ?? ''), 0, 18)) ?>…</code></td>
          <td><?= $hasKey ? '<code>' . e(substr(strval($key['signature'] ?? $key['key_signature'] ?? ''), 0, 18)) . '…</code>' : '—' ?></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</section>
<?php layout_footer(); ?>
