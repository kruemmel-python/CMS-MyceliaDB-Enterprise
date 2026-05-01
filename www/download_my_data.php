<?php
require_once __DIR__ . '/bootstrap.php';
require_login();

$response = call_mycelia('export_my_data', []);
if (($response['status'] ?? '') !== 'ok') {
    flash($response['message'] ?? 'Datenexport fehlgeschlagen.', 'error');
    redirect('privacy.php');
}
$export = $response['export'] ?? [];
$filename = preg_replace('/[^a-zA-Z0-9_.-]/', '_', strval($response['filename'] ?? 'myceliadb-export.json'));
$raw = json_encode($export, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
if ($raw === false) {
    flash('Datenexport konnte nicht serialisiert werden.', 'error');
    redirect('privacy.php');
}
header('Content-Type: application/json; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $filename . '"');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');
echo $raw;
