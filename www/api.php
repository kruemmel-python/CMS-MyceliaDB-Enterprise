<?php
/**
 * MyceliaDB Enterprise Web API Bridge.
 * No PDO, no MySQL, no SQLite. All application state is delegated to mycelia_platform.py.
 */
function mycelia_web_cleartext_read_commands(): array {
    return [
        'get_profile',
        'list_forum_threads',
        'get_forum_thread',
        'list_comments',
        'list_blogs',
        'get_blog',
        'list_blog_posts',
        'get_blog_post',
        'admin_overview',
        'list_users',
        'webauthn_challenge_begin',
        'security_evolution_status',
        'telemetry_snapshot',
        'e2ee_inbox',
        'e2ee_public_key_lookup',
    ];
}

function call_mycelia(string $command, array $payload = []): array {
    $url = getenv('MYCELIA_API_URL') ?: 'http://127.0.0.1:9999';

    // UI rendering must display values reconstructed from MyceliaDB.  In strict
    // VRAM mode the Engine redacts normal responses unless the web UI explicitly
    // asks for human-display reconstruction.  This flag is allowed only for read
    // endpoints and never for audit/certification commands.
    if (in_array($command, mycelia_web_cleartext_read_commands(), true)
        && (getenv('MYCELIA_PHP_CLEAR_TEXT_UI') ?: '1') !== '0') {
        $payload['_web_ui_cleartext_response'] = true;
        $payload['allow_cleartext_response'] = true;
        if ($command === 'get_profile') {
            $payload['allow_cleartext_profile'] = true;
        }
    }

    // Zero-Logic Gateway transport binding: PHP does not authorize, but it may
    // forward opaque engine session material so the Engine can validate/rotate it.
    if (session_status() === PHP_SESSION_ACTIVE && !isset($payload['engine_session_handle'])) {
        if (!empty($_SESSION['mycelia_engine_session_handle']) && !empty($_SESSION['mycelia_engine_request_token'])) {
            $payload['engine_session_handle'] = strval($_SESSION['mycelia_engine_session_handle']);
            $payload['engine_request_token'] = strval($_SESSION['mycelia_engine_request_token']);
        }
    }
    $data = [
        'command' => $command,
        'action' => $command,
        'payload' => $payload
    ];
    $headers = "Content-Type: application/json\r\n";
    $tokenFile = getenv('MYCELIA_API_TOKEN_FILE') ?: (__DIR__ . '/../html/keys/local_transport.token');
    if (is_file($tokenFile)) {
        $token = trim(strval(@file_get_contents($tokenFile)));
        if ($token !== '') {
            $headers .= "X-Mycelia-Local-Token: " . $token . "\r\n";
        }
    }
    $contextOptions = [
        'http' => [
            'header' => $headers,
            'method' => 'POST',
            'timeout' => 25,
            'content' => json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
        ]
    ];
    if (str_starts_with($url, 'https://')) {
        $cafile = getenv('MYCELIA_API_CA_FILE') ?: '';
        $contextOptions['ssl'] = [
            'verify_peer' => $cafile !== '',
            'verify_peer_name' => false,
            'allow_self_signed' => $cafile === '',
        ];
        if ($cafile !== '') {
            $contextOptions['ssl']['cafile'] = $cafile;
        }
    }
    $context = stream_context_create($contextOptions);
    $result = @file_get_contents($url, false, $context);
    if ($result === false) {
        return [
            'status' => 'error',
            'message' => 'MyceliaDB Engine nicht erreichbar. Starte: python html/mycelia_platform.py'
        ];
    }
    $decoded = json_decode($result, true);
    if (is_array($decoded)) {
        if (function_exists('mycelia_apply_engine_session')) {
            mycelia_apply_engine_session($decoded);
        }
        return $decoded;
    }
    return ['status' => 'error', 'message' => 'Ungültige Engine-Antwort'];
}

function require_mycelia_ok(array $response): array {
    if (($response['status'] ?? 'error') !== 'ok') {
        $msg = htmlspecialchars($response['message'] ?? 'Unbekannter Mycelia-Fehler', ENT_QUOTES, 'UTF-8');
        die("<main class='panel'><h1>MYCELIA ERROR</h1><p class='error'>{$msg}</p></main>");
    }
    return $response;
}

function mycelia_apply_engine_session(array $response): void {
    if (session_status() === PHP_SESSION_ACTIVE && isset($response['engine_session']) && is_array($response['engine_session'])) {
        $_SESSION['mycelia_engine_session_handle'] = strval($response['engine_session']['handle'] ?? '');
        $_SESSION['mycelia_engine_request_token'] = strval($response['engine_session']['request_token'] ?? '');
        $_SESSION['mycelia_engine_sequence'] = intval($response['engine_session']['sequence'] ?? 0);
        $_SESSION['mycelia_engine_expires_at'] = floatval($response['engine_session']['expires_at'] ?? 0);
    }
    if (session_status() === PHP_SESSION_ACTIVE && isset($response['permissions']) && is_array($response['permissions'])) {
        $_SESSION['mycelia_permissions'] = array_values(array_map('strval', $response['permissions']));
    }
}

function call_mycelia_direct_ingest(string $op, string $sealed, array $actorContext = []): array {
    $response = call_mycelia('direct_ingest', [
        'op' => $op,
        'sealed' => $sealed,
        'actor_context' => $actorContext,
    ]);
    mycelia_apply_engine_session($response);
    return $response;
}

function mycelia_ingest_manifest(string $op = ''): array {
    $payload = [];
    if ($op !== '') {
        $payload['op'] = $op;
    }
    return call_mycelia('direct_ingest_manifest', $payload);
}

?>
