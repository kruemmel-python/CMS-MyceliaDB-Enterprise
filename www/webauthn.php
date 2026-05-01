<?php
require_once __DIR__ . '/bootstrap.php';
require_login();
handle_direct_ingest('webauthn.php');
layout_header('FIDO2 / WebAuthn');
?>
<section class="card">
  <h1>FIDO2 / WebAuthn Bridge</h1>
  <p>Registriert Hardware-/Plattform-Credentials als Mycelia-Attraktor. PHP bleibt Transport-Gateway.</p>
  <button type="button" id="webauthn-register">Credential im Browser erzeugen</button>
  <form method="post" data-direct-op="webauthn_register_credential" id="webauthn-form">
    <input type="hidden" name="challenge_id" id="webauthn_challenge_id">
    <input type="hidden" name="credential_id_b64url" id="webauthn_credential_id">
    <input type="hidden" name="public_key_cose_b64" id="webauthn_public_key">
    <input type="hidden" name="sign_count" value="0">
    <button>Credential speichern</button>
  </form>
</section>
<?php layout_footer(); ?>
