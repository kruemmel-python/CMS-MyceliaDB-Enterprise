<?php
declare(strict_types=1);
session_start();
require_once __DIR__ . '/api.php';
header('Content-Type: application/json; charset=utf-8');
$op = isset($_GET['op']) ? strval($_GET['op']) : '';
$manifest = mycelia_ingest_manifest($op);
if (($manifest['clear_engine_session'] ?? false) === true && session_status() === PHP_SESSION_ACTIVE) {
    unset(
        $_SESSION['mycelia_engine_session_handle'],
        $_SESSION['mycelia_engine_request_token'],
        $_SESSION['mycelia_engine_sequence'],
        $_SESSION['mycelia_engine_expires_at'],
        $_SESSION['mycelia_signature'],
        $_SESSION['mycelia_username'],
        $_SESSION['mycelia_role'],
        $_SESSION['mycelia_permissions']
    );
}
if (session_status() === PHP_SESSION_ACTIVE && !empty($_SESSION['mycelia_engine_request_token'])) {
    $manifest['engine_request_token'] = strval($_SESSION['mycelia_engine_request_token']);
    $manifest['engine_session_binding'] = 'sealed-request-token';
}
echo json_encode($manifest, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
