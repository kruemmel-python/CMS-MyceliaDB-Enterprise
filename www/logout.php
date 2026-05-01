<?php
require_once __DIR__ . '/bootstrap.php';
if (!empty($_SESSION['mycelia_engine_session_handle'])) {
    call_mycelia('logout_session', engine_session_context());
}
session_destroy();
session_start();
flash('Abgemeldet. Die flüchtige Engine-Session wurde gelöscht.', 'info');
redirect('index.php');
?>
