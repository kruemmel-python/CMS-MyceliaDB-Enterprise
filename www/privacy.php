<?php
require_once __DIR__ . '/bootstrap.php';
require_login();

if (!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])) {
    $op = strval($_POST['direct_op']);
    $response = call_mycelia_direct_ingest($op, strval($_POST['sealed_ingest']), direct_actor_context());
    if ($op === 'delete_my_account' && (($response['status'] ?? '') === 'ok')) {
        $_SESSION = [];
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_destroy();
        }
        session_start();
        flash($response['message'] ?? 'Account wurde gelöscht.', 'info');
        redirect('index.php');
    }
    flash($response['message'] ?? 'Datenschutz-Aktion fehlgeschlagen.', ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('privacy.php');
}

layout_header(txt('privacy.title'));
?>
<section class="panel">
    <h1><?= e(txt('privacy.title')) ?></h1>
    <p class="muted"><?= e(txt('privacy.subtitle')) ?></p>
    <p class="warn"><?= e(txt('privacy.warning')) ?></p>
</section>

<section class="split" style="margin-top:22px">
    <div class="panel">
        <h2><?= e(txt('privacy.export_title')) ?></h2>
        <p><?= e(txt('privacy.export_body')) ?></p>
        <p><a class="button" href="download_my_data.php"><?= e(txt('privacy.export_button')) ?></a></p>
        <p class="muted mono">Format: MYCELIA_SUBJECT_EXPORT_V1 · JSON · session-bound read</p>
    </div>

    <div class="panel danger-zone">
        <h2><?= e(txt('privacy.delete_title')) ?></h2>
        <p><?= e(txt('privacy.delete_body')) ?></p>
        <form method="post" data-direct-op="delete_my_account" onsubmit="return confirm('Account wirklich endgültig löschen?')">
            <label><?= e(txt('privacy.delete_confirm_label')) ?></label>
            <input name="confirm_delete" autocomplete="off" placeholder="DELETE">
            <label><?= e(txt('privacy.password_label')) ?></label>
            <input name="password" type="password" autocomplete="current-password">
            <input type="hidden" name="delete_mode" value="hard-purge">
            <button class="danger"><?= e(txt('privacy.delete_button')) ?></button>
        </form>
    </div>
</section>
<?php layout_footer(); ?>
