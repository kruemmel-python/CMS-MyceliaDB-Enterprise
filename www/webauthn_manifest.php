<?php
declare(strict_types=1);
require_once __DIR__ . '/bootstrap.php';
header('Content-Type: application/json; charset=utf-8');
if (!is_logged_in()) {
    echo json_encode(['status' => 'error', 'message' => 'login required']);
    exit;
}
echo json_encode(call_mycelia('webauthn_challenge_begin', engine_session_context()), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
