<?php
declare(strict_types=1);
session_start();
require_once __DIR__ . '/api.php';
require_once __DIR__ . '/site_texts.php';

function mycelia_scalar_text(mixed $value, string $fallback = ''): string {
    if ($value === null) {
        return $fallback;
    }
    if (is_bool($value)) {
        return $value ? 'true' : 'false';
    }
    if (is_int($value) || is_float($value) || is_string($value)) {
        return strval($value);
    }
    if (is_array($value)) {
        // Engine safe-fragment: already escaped by the Engine for HTML context.
        // Used for future native/VRAM response paths.
        if (($value['policy'] ?? '') === 'engine-context-escaped-html-text') {
            return strval($value['text'] ?? $fallback);
        }

        // Strict-VRAM redaction objects have no policy, but carry a display text.
        // Never call strval(array): that creates PHP warnings and can corrupt UI.
        if (array_key_exists('text', $value) && !is_array($value['text'])) {
            return strval($value['text']);
        }
        if (array_key_exists('value', $value) && !is_array($value['value'])) {
            return strval($value['value']);
        }
        if (array_key_exists('message', $value) && !is_array($value['message'])) {
            return strval($value['message']);
        }

        // Scalar list: useful for small status/capability arrays.
        $parts = [];
        $isScalarList = array_keys($value) === range(0, max(0, count($value) - 1));
        if ($isScalarList) {
            foreach ($value as $item) {
                if (is_scalar($item) || $item === null) {
                    $parts[] = strval($item ?? '');
                } else {
                    $parts = [];
                    break;
                }
            }
            if ($parts) {
                return implode(', ', $parts);
            }
        }

        // Structured arrays should not be implicitly rendered as "Array".
        // Admin JSON blocks call json_encode before e(), so this fallback should
        // only appear where a template accidentally receives structured data.
        return '[structured-data]';
    }
    if (is_object($value) && method_exists($value, '__toString')) {
        return strval($value);
    }
    return $fallback;
}

function e(mixed $value): string {
    if (is_array($value) && ($value['policy'] ?? '') === 'engine-context-escaped-html-text') {
        return mycelia_scalar_text($value);
    }
    return htmlspecialchars(mycelia_scalar_text($value), ENT_QUOTES, 'UTF-8');
}

function render_engine_markdown(mixed $fragment, mixed $fallback = ''): void {
    // v1.21.25: PHP is public-Markdown-blind again.
    // Preferred path: Engine returns a client-side encrypted Markdown vault.
    // PHP emits only a ciphertext capsule for browser-side decrypt+render.
    if (is_array($fragment) && ($fragment['version'] ?? '') === 'client_markdown_vault_v1') {
        $json = json_encode($fragment, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
        $b64 = base64_encode($json ?: '{}');
        echo '<article class="markdown-body markdown-vault" data-markdown-vault="' . e($b64) . '"><p class="muted">Markdown wird lokal im Browser entschlüsselt …</p></article>';
        return;
    }
    if (is_array($fragment) && ($fragment['policy'] ?? '') === 'engine-safe-markdown-html') {
        // Legacy compatibility only. New web-created Forum/Blog content should not use this path.
        echo strval($fragment['text'] ?? '');
        return;
    }
    // No plaintext fallback for public pages unless a legacy direct-engine caller explicitly provided it.
    $plain = mycelia_scalar_text($fallback !== '' ? $fallback : $fragment);
    if ($plain !== '') {
        echo '<article class="markdown-body legacy-markdown"><p>' . nl2br(e($plain)) . '</p></article>';
    } else {
        echo '<article class="markdown-body"><p class="muted">Kein clientseitiges Markdown-Paket vorhanden.</p></article>';
    }
}

function mycelia_url_component(mixed $value): string {
    return urlencode(mycelia_scalar_text($value));
}

function mycelia_identity(mixed $value): string {
    // IDs/signatures are expected to be scalar strings.  In strict-redaction
    // mode the Engine may return structured safe fragments for display fields;
    // those are not valid route IDs.  Returning an empty ID is safer than
    // rendering/transporting an implicit "Array" value.
    if (is_string($value) || is_int($value) || is_float($value)) {
        return strval($value);
    }
    return '';
}


function ui_excerpt(mixed $value, int $width = 100, string $ellipsis = '...'): string {
    $text = mycelia_scalar_text($value);
    if ($width <= 0) {
        return '';
    }
    if (function_exists('mb_strimwidth')) {
        return mb_strimwidth($text, 0, $width, $ellipsis, 'UTF-8');
    }
    if (function_exists('preg_split')) {
        $chars = preg_split('//u', $text, -1, PREG_SPLIT_NO_EMPTY);
        if (is_array($chars)) {
            if (count($chars) <= $width) {
                return $text;
            }
            return implode('', array_slice($chars, 0, max(0, $width - strlen($ellipsis)))) . $ellipsis;
        }
    }
    if (strlen($text) <= $width) {
        return $text;
    }
    return substr($text, 0, max(0, $width - strlen($ellipsis))) . $ellipsis;
}

function mycelia_redact_admin_report(mixed $value): mixed {
    $sensitiveKeys = [
        'auth_pattern' => true,
        'password' => true,
        'password_hash' => true,
        'profile_seed' => true,
        'profile_blob' => true,
        'content_seed' => true,
        'content_blob' => true,
        'seed' => true,
        'blob' => true,
        'request_token' => true,
        'engine_request_token' => true,
        'sealed' => true,
        'sealed_ingest' => true,
        'key_b64' => true,
        'iv_b64' => true,
        'ciphertext_b64' => true,
    ];
    $shortKeys = [
        'handle' => true,
        'engine_session_handle' => true,
        'signature' => true,
        'actor_signature' => true,
        'author_signature' => true,
        'owner_signature' => true,
        'target_signature' => true,
    ];
    if (is_array($value)) {
        $out = [];
        foreach ($value as $k => $v) {
            $ks = is_string($k) ? $k : strval($k);
            if (isset($sensitiveKeys[$ks])) {
                // Omit secret-bearing fields from dashboard JSON entirely.
                continue;
            } elseif ($ks === 'engine_session' && is_array($v)) {
                $out[$k] = [
                    'handle' => mycelia_short_identifier(strval($v['handle'] ?? '')),
                    'request_token' => '[redacted:admin-report]',
                    'sequence' => $v['sequence'] ?? null,
                    'expires_at' => $v['expires_at'] ?? null,
                    'rotated' => $v['rotated'] ?? null,
                ];
            } elseif (isset($shortKeys[$ks]) && is_string($v) && strlen($v) > 18) {
                $out[$k] = mycelia_short_identifier($v);
            } else {
                $out[$k] = mycelia_redact_admin_report($v);
            }
        }
        return $out;
    }
    return $value;
}

function mycelia_short_identifier(string $value): string {
    if ($value === '' || strlen($value) <= 18) {
        return $value;
    }
    return substr($value, 0, 10) . '…' . substr($value, -6);
}

function mycelia_admin_json(mixed $value): string {
    $redacted = mycelia_redact_admin_report($value);
    $json = json_encode($redacted, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    return $json === false ? '{}' : $json;
}

function redirect(string $path): never {
    header("Location: {$path}");
    exit;
}

function flash(mixed $message = null, string $type = 'info'): ?array {
    if ($message !== null) {
        $_SESSION['_flash'] = ['message' => mycelia_scalar_text($message), 'type' => mycelia_scalar_text($type)];
        return null;
    }
    $value = $_SESSION['_flash'] ?? null;
    unset($_SESSION['_flash']);
    return $value;
}

function is_logged_in(): bool {
    return !empty($_SESSION['mycelia_engine_session_handle']) && !empty($_SESSION['mycelia_engine_request_token']);
}

function is_direct_ingest_post(): bool {
    return ($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST'
        && !empty($_POST['sealed_ingest'])
        && !empty($_POST['direct_op']);
}

function current_signature(): string {
    return mycelia_identity($_SESSION['mycelia_signature'] ?? '');
}

function current_username(): string {
    return mycelia_scalar_text($_SESSION['mycelia_username'] ?? 'anonymous', 'anonymous');
}

function current_role(): string {
    return mycelia_scalar_text($_SESSION['mycelia_role'] ?? (current_username() === 'admin' ? 'admin' : 'user'), 'user');
}

function current_permissions(): array {
    $perms = $_SESSION['mycelia_permissions'] ?? [];
    return is_array($perms) ? array_values(array_map('strval', $perms)) : [];
}

function has_permission(string $permission): bool {
    return current_role() === 'admin' || in_array($permission, current_permissions(), true);
}

function is_admin(): bool {
    return current_role() === 'admin' || current_username() === 'admin' || has_permission('admin.access');
}

function require_login(): void {
    if (!is_logged_in()) {
        flash('Bitte zuerst einloggen.', 'warn');
        redirect('index.php');
    }
    // Critical Direct-Ingest token discipline:
    // A sealed form already contains the one-time Engine token that was fetched
    // immediately before browser-side sealing.  If require_login() rotated the
    // session here before handle_direct_ingest() runs, the sealed token would be
    // stale and every create/delete/audit form would fail with:
    // "Request-Token passt nicht zum flüchtigen Engine-Attraktor."
    //
    // For sealed POSTs PHP only checks that an opaque Engine session exists.
    // The Engine performs the real authorization inside direct_ingest().
    if (is_direct_ingest_post()) {
        return;
    }
    $validation = call_mycelia('validate_session', engine_session_context());
    if (($validation['status'] ?? '') !== 'ok') {
        $_SESSION = [];
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_destroy();
        }
        session_start();
        flash($validation['message'] ?? 'Engine-Session abgelaufen. Bitte neu einloggen.', 'warn');
        redirect('index.php');
    }
    mycelia_apply_engine_session($validation);
    $_SESSION['mycelia_signature'] = mycelia_identity($validation['signature'] ?? '');
    $_SESSION['mycelia_username'] = mycelia_scalar_text($validation['username'] ?? 'anonymous', 'anonymous');
    $_SESSION['mycelia_role'] = mycelia_scalar_text($validation['role'] ?? 'user', 'user');
    $_SESSION['mycelia_permissions'] = is_array($validation['permissions'] ?? null) ? array_values(array_map('strval', $validation['permissions'])) : [];
}

function require_admin(): void {
    require_login();
    if (!is_admin()) {
        flash('Admin-Rechte erforderlich.', 'error');
        redirect('index.php');
    }
}

function engine_session_context(): array {
    return [
        'engine_session_handle' => strval($_SESSION['mycelia_engine_session_handle'] ?? ''),
        'engine_request_token' => strval($_SESSION['mycelia_engine_request_token'] ?? ''),
    ];
}

function direct_actor_context(): array {
    // Zero-Logic Gateway: PHP forwards only the opaque session handle. The
    // one-time request token is sealed inside the browser-encrypted envelope,
    // so a cross-site form post cannot borrow PHP's server-side token.
    return [
        'engine_session_handle' => strval($_SESSION['mycelia_engine_session_handle'] ?? ''),
    ];
}

function handle_direct_ingest(string $redirectPath, ?callable $onOk = null): void {
    if (empty($_POST['sealed_ingest']) || empty($_POST['direct_op'])) {
        return;
    }
    $response = call_mycelia_direct_ingest(strval($_POST['direct_op']), strval($_POST['sealed_ingest']), direct_actor_context());
    if (($response['status'] ?? '') === 'ok') {
        if ($onOk !== null) {
            $onOk($response);
        }
        flash($response['message'] ?? 'Direct GPU Ingest erfolgreich verarbeitet.', 'info');
    } else {
        flash($response['message'] ?? 'Direct GPU Ingest fehlgeschlagen.', 'error');
    }
    redirect($redirectPath);
}

function actor_payload(): array {
    // Legacy helper retained for read-only compatibility; mutating commands are
    // denied by enforce_zero_logic_gateway() unless sealed through Direct Ingest.
    return engine_session_context();
}

function enforce_zero_logic_gateway(): void {
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'POST') {
        return;
    }
    if (!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])) {
        return;
    }
    $allowedControlPosts = [
        // Admin VRAM/Audit controls are deliberately non-Direct-Ingest because
        // they do not carry user content, credentials, profile data or plugin
        // manifests. They only trigger engine-side status/audit commands or
        // submit a scanner JSON evidence report.
        'run_residency_manifest',
        'submit_memory_probe_report',
        'run_restore_residency_audit',
        'run_native_gpu_report',
        'run_native_gpu_selftest',
        'run_strict_certification',
        'run_vram_evidence_bundle',
        'run_vram_audit',
        'run_enterprise_v120_report',
    ];
    foreach ($allowedControlPosts as $key) {
        if (isset($_POST[$key])) {
            return;
        }
    }
    http_response_code(400);
    die("<main class='panel'><h1>Zero-Logic Gateway</h1><p class='error'>Klartext-POSTs sind deaktiviert. Diese Plattform akzeptiert nur browserseitig versiegelte Direct-GPU-Ingest-Pakete.</p></main>");
}

enforce_zero_logic_gateway();


function mycelia_site_text_overrides(): array {
    static $cache = null;
    if ($cache !== null) return $cache;
    $cache = [];
    $response = call_mycelia('list_site_texts', []);
    if (($response['status'] ?? '') === 'ok' && isset($response['texts']) && is_array($response['texts'])) {
        foreach ($response['texts'] as $key => $row) {
            if (is_array($row) && array_key_exists('value', $row)) {
                $cache[mycelia_scalar_text($key)] = mycelia_scalar_text($row['value']);
            }
        }
    }
    return $cache;
}

function txt(string $key, ?string $fallback = null): string {
    $defaults = MYCELIA_SITE_TEXT_DEFAULTS;
    $overrides = mycelia_site_text_overrides();
    if (array_key_exists($key, $overrides)) return $overrides[$key];
    if (array_key_exists($key, $defaults)) return mycelia_scalar_text($defaults[$key]);
    return $fallback ?? $key;
}

function site_text_catalog(): array {
    return MYCELIA_SITE_TEXT_DEFAULTS;
}


function render_media_gallery(mixed $media): void {
    if (!is_array($media) || count($media) === 0) {
        return;
    }
    echo "<div class='media-gallery'>";
    foreach ($media as $item) {
        if (!is_array($item)) continue;
        $kind = mycelia_scalar_text($item['media_kind'] ?? '');
        $title = mycelia_scalar_text($item['title'] ?? $item['filename'] ?? 'Medium');
        echo "<figure class='media-card'>";
        if ($kind === 'image' && !empty($item['data_uri'])) {
            echo "<img src='" . e($item['data_uri']) . "' alt='" . e($title) . "' loading='lazy'>";
        } elseif ($kind === 'embed' && is_array($item['embed'] ?? null)) {
            $provider = mycelia_scalar_text($item['embed']['provider'] ?? '');
            $embedId = mycelia_scalar_text($item['embed']['embed_id'] ?? '');
            $safeUrl = mycelia_scalar_text($item['embed']['safe_url'] ?? '');
            if ($provider === 'youtube' && $embedId !== '') {
                echo "<iframe loading='lazy' src='https://www.youtube-nocookie.com/embed/" . e($embedId) . "' title='" . e($title) . "' allowfullscreen sandbox='allow-scripts allow-same-origin allow-presentation'></iframe>";
            } elseif ($provider === 'vimeo' && $embedId !== '') {
                echo "<iframe loading='lazy' src='https://player.vimeo.com/video/" . e($embedId) . "' title='" . e($title) . "' allowfullscreen sandbox='allow-scripts allow-same-origin allow-presentation'></iframe>";
            } elseif ($provider === 'external_image' && $safeUrl !== '') {
                echo "<img src='" . e($safeUrl) . "' alt='" . e($title) . "' loading='lazy' referrerpolicy='no-referrer'>";
            } elseif ($safeUrl !== '') {
                echo "<a href='" . e($safeUrl) . "' rel='noopener noreferrer nofollow' target='_blank'>" . e($title) . "</a>";
            }
        } else {
            echo "<div class='muted'>Medium nicht darstellbar.</div>";
        }
        echo "<figcaption>" . e($title) . "</figcaption>";
        echo "</figure>";
    }
    echo "</div>";
}

function media_upload_fields(string $targetSignature = '', string $targetType = ''): void {
    if ($targetSignature !== '') {
        echo "<input type='hidden' name='target_signature' value='" . e($targetSignature) . "'>";
    }
    if ($targetType !== '') {
        echo "<input type='hidden' name='target_type' value='" . e($targetType) . "'>";
    }
    echo "<label>Bild anhängen (JPEG, PNG, GIF, WebP · max 3 MB)</label>";
    echo "<input type='file' name='media' accept='image/png,image/jpeg,image/gif,image/webp' data-media-prefix='media' data-max-bytes='3145728'>";
    echo "<label>Oder sicherer Medien-Link (YouTube, Vimeo, HTTPS-Bild)</label>";
    echo "<input name='embed_url' placeholder='https://youtu.be/... oder https://example.com/bild.webp'>";
    echo "<label>Medien-Titel</label>";
    echo "<input name='media_title' maxlength='240' placeholder='Optionale Bild-/Video-Beschreibung'>";
}


function fun_plugin_enabled(string $pluginId): bool {
    static $enabledMap = null;
    if ($enabledMap === null) {
        $enabledMap = [];
        if (is_logged_in()) {
            $dashboard = call_mycelia('fun_plugin_dashboard', engine_session_context());
            $ids = is_array($dashboard['enabled_plugin_ids'] ?? null) ? $dashboard['enabled_plugin_ids'] : [];
            foreach ($ids as $id) {
                $enabledMap[(string)$id] = true;
            }
        }
    }
    return isset($enabledMap[$pluginId]);
}

function reaction_sticker_catalog(): array {
    return [
        'like' => ['emoji' => '👍', 'label' => 'Like'],
        'dislike' => ['emoji' => '👎', 'label' => 'Dislike'],
        'fire' => ['emoji' => '🔥', 'label' => 'Stark'],
        'funny' => ['emoji' => '😂', 'label' => 'Lustig'],
        'heart' => ['emoji' => '💚', 'label' => 'Herz'],
        'insightful' => ['emoji' => '💡', 'label' => 'Interessant'],
        'thanks' => ['emoji' => '❤️', 'label' => 'Danke'],
        'thinking' => ['emoji' => '🤔', 'label' => 'Nachdenklich'],
    ];
}

function reaction_breakdown(mixed $content): array {
    if (is_array($content) && isset($content['reaction_breakdown']) && is_array($content['reaction_breakdown'])) {
        return $content['reaction_breakdown'];
    }
    return [];
}

function active_reaction_catalog(): array {
    $catalog = reaction_sticker_catalog();
    if (fun_plugin_enabled('reaction_stickers')) {
        return $catalog;
    }
    return array_intersect_key($catalog, array_flip(['like', 'dislike']));
}

function render_reaction_summary(mixed $content): void {
    $breakdown = reaction_breakdown($content);
    echo "<div class='meta reaction-summary'>";
    foreach (active_reaction_catalog() as $id => $meta) {
        $count = intval($breakdown[$id] ?? (($id === 'like') ? ($content['likes'] ?? 0) : (($id === 'dislike') ? ($content['dislikes'] ?? 0) : 0)));
        echo "<span>" . e($meta['emoji'] . ' ' . $meta['label'] . ' ' . $count) . "</span>";
    }
    echo "</div>";
}

function render_reaction_sticker_form(string $targetSignature, string $targetType, array $hidden = []): void {
    if ($targetSignature === '') {
        return;
    }
    echo "<form method='post' class='actions reaction-stickers' data-direct-op='react_content'>";
    foreach ($hidden as $name => $value) {
        echo "<input type='hidden' name='" . e($name) . "' value='" . e(strval($value)) . "'>";
    }
    echo "<input type='hidden' name='target_signature' value='" . e($targetSignature) . "'>";
    echo "<input type='hidden' name='target_type' value='" . e($targetType) . "'>";
    foreach (active_reaction_catalog() as $id => $meta) {
        echo "<button name='reaction' value='" . e($id) . "' class='secondary' title='" . e($meta['label']) . "'>" . e($meta['emoji'] . ' ' . $meta['label']) . "</button>";
    }
    echo "</form>";
}

function blog_mood_theme_catalog(): array {
    return [
        'security' => ['emoji' => '🛡️', 'label' => 'Security'],
        'research' => ['emoji' => '🧪', 'label' => 'Forschung'],
        'gaming' => ['emoji' => '🎮', 'label' => 'Gaming'],
        'nature' => ['emoji' => '🌿', 'label' => 'Natur'],
        'creative' => ['emoji' => '🎨', 'label' => 'Kreativ'],
        'scifi' => ['emoji' => '🌌', 'label' => 'Sci-Fi'],
    ];
}

function render_blog_theme_select(string $selected = ''): void {
    if (!fun_plugin_enabled('blog_mood_themes')) {
        return;
    }
    echo "<label>Blog Mood Theme</label>";
    echo "<select name='blog_theme'>";
    echo "<option value=''>Kein Theme</option>";
    foreach (blog_mood_theme_catalog() as $id => $meta) {
        $sel = ($selected === $id) ? " selected" : "";
        echo "<option value='" . e($id) . "'" . $sel . ">" . e($meta['emoji'] . ' ' . $meta['label']) . "</option>";
    }
    echo "</select>";
}

function render_blog_theme_badge(mixed $blog): void {
    if (!fun_plugin_enabled('blog_mood_themes')) {
        return;
    }
    if (!is_array($blog)) {
        return;
    }
    $theme = mycelia_scalar_text($blog['blog_theme'] ?? '');
    if ($theme === '') {
        return;
    }
    $catalog = blog_mood_theme_catalog();
    $meta = $catalog[$theme] ?? null;
    if (!$meta) {
        return;
    }
    echo "<span class='badge blog-theme'>" . e($meta['emoji'] . ' ' . $meta['label']) . "</span>";
}


function layout_header(mixed $title): void {
    $flash = flash();
    $navAuth = is_logged_in()
        ? '<a href="profile.php">' . e(txt('nav.profile')) . '</a><a href="profile.php#messages">Nachrichten</a><a href="fun.php">Spaß-Plugins</a><a href="dashboard.php">Live-Dashboard</a><a href="e2ee.php">E2EE</a><a href="webauthn.php">WebAuthn</a><a href="forum.php">' . e(txt('nav.forum')) . '</a><a href="blogs.php">' . e(txt('nav.blogs')) . '</a><a href="my_blog.php">' . e(txt('nav.my_blog')) . '</a><a href="privacy.php">' . e(txt('nav.privacy')) . '</a>' . (is_admin() ? '<a href="plugins.php">' . e(txt('nav.plugins')) . '</a><a href="admin.php">' . e(txt('nav.admin')) . '</a>' : '') . '<a href="logout.php">' . e(txt('nav.logout')) . '</a>'
        : '<a href="index.php">' . e(txt('nav.login')) . '</a>';
    echo "<!doctype html><html lang='de'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>";
    echo "<title>" . e(mycelia_scalar_text($title, "MyceliaDB")) . " | MyceliaDB</title><link rel='stylesheet' href='assets/style.css'><script defer src='assets/client-markdown-vault.js'></script><script defer src='assets/markdown-copy.js'></script></head><body>";
    echo "<header class='topbar'><a class='brand' href='index.php'>" . e(txt('brand.name')) . "</a><nav>{$navAuth}</nav></header>";
    if ($flash) {
        echo "<div class='flash " . e($flash['type']) . "'>" . e($flash['message']) . "</div>";
    }
    $pageClass = 'page';
    if (!empty($GLOBALS['MYCELIA_PAGE_CLASS']) && is_string($GLOBALS['MYCELIA_PAGE_CLASS'])) {
        $safeClass = preg_replace('/[^a-zA-Z0-9_\- ]/', '', $GLOBALS['MYCELIA_PAGE_CLASS']);
        $pageClass .= ' ' . trim((string)$safeClass);
    }
    echo "<main class='" . e($pageClass) . "'>";
}


function e2ee_safe_jwk_text(mixed $jwk): string {
    if (is_string($jwk)) {
        return $jwk;
    }
    if (is_array($jwk)) {
        return json_encode($jwk, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) ?: '';
    }
    return '';
}

function e2ee_latest_own_public_key_jwk(array $myKeys): string {
    $keys = is_array($myKeys['keys'] ?? null) ? $myKeys['keys'] : [];
    if (!$keys) {
        return '';
    }
    usort($keys, fn($a, $b) => floatval($b['created_at'] ?? 0) <=> floatval($a['created_at'] ?? 0));
    return e2ee_safe_jwk_text($keys[0]['public_key_jwk'] ?? '');
}

function e2ee_render_message_card(array $message, string $mailbox): void {
    $signature = mycelia_identity($message['signature'] ?? '');
    $cipher = mycelia_scalar_text($message['ciphertext_b64'] ?? '');
    $nonce = mycelia_scalar_text($message['nonce_b64'] ?? '');
    $eph = e2ee_safe_jwk_text($message['eph_public_jwk'] ?? '');
    $aad = mycelia_scalar_text($message['aad'] ?? 'mycelia-e2ee-v1');
    $sender = mycelia_scalar_text($message['sender_username'] ?? '');
    $senderSig = mycelia_identity($message['sender_signature'] ?? '');
    $recipient = mycelia_scalar_text($message['recipient_username'] ?? '');
    $recipientSig = mycelia_identity($message['recipient_signature'] ?? '');
    $title = $mailbox === 'outbox'
        ? ('An ' . ($recipient !== '' ? $recipient : substr($recipientSig, 0, 12) . '…'))
        : ('Von ' . ($sender !== '' ? $sender : substr($senderSig, 0, 12) . '…'));
    echo "<article class='message-card' data-e2ee-message='1'"
        . " data-ciphertext-b64='" . e($cipher) . "'"
        . " data-nonce-b64='" . e($nonce) . "'"
        . " data-eph-public-jwk='" . e($eph) . "'"
        . " data-aad='" . e($aad) . "'"
        . " data-sender-signature='" . e($senderSig) . "'"
        . " data-sender-username='" . e($sender) . "'>";
    echo "<div class='message-head'><strong>" . e($title) . "</strong><span class='muted'>" . e(fmt_time($message['created_at'] ?? null)) . "</span></div>";
    echo "<p class='muted mono'>MSG " . e(substr($signature, 0, 18)) . "… · " . e($mailbox) . "</p>";
    echo "<pre data-e2ee-plaintext hidden class='message-plaintext'></pre>";
    echo "<div class='actions'>";
    echo "<button type='button' data-e2ee-decrypt='1'>Lesen</button>";
    if ($mailbox === 'inbox') {
        echo "<button type='button' class='secondary' data-e2ee-reply='1'>Antworten</button>";
    }
    echo "<form method='post' data-direct-op='e2ee_delete_message' onsubmit=\"return confirm('Nachricht aus dieser Box löschen?')\">";
    echo "<input type='hidden' name='signature' value='" . e($signature) . "'>";
    echo "<input type='hidden' name='mailbox' value='" . e($mailbox) . "'>";
    echo "<button class='danger'>Löschen</button>";
    echo "</form>";
    echo "</div></article>";
}

function e2ee_render_mailbox(array $messages, string $mailbox): void {
    if (!$messages) {
        echo "<p class='muted'>Keine Nachrichten.</p>";
        return;
    }
    echo "<div class='message-list'>";
    foreach ($messages as $message) {
        if (is_array($message)) {
            e2ee_render_message_card($message, $mailbox);
        }
    }
    echo "</div>";
}


function layout_footer(): void {
    echo "</main><footer class='footer'>" . e(txt('footer.text')) . "</footer><script src='assets/e2ee.js' defer></script><script src='assets/direct-ingest.js' defer></script><script src='assets/webauthn.js' defer></script><script src='assets/markdown-copy.js' defer></script></body></html>";
}

function fmt_time(mixed $ts): string {
    if (is_array($ts)) {
        $ts = mycelia_scalar_text($ts);
    }
    if (!$ts || !is_numeric($ts)) return 'n/a';
    return date('d.m.Y H:i', (int)floatval($ts));
}

function ownership_actions(mixed $ownerSignature, mixed $editUrl, mixed $deleteName, mixed $signature): string {
    $ownerSignature = mycelia_identity($ownerSignature);
    $signature = mycelia_identity($signature);
    $deleteName = mycelia_scalar_text($deleteName);
    $editUrl = mycelia_scalar_text($editUrl);
    if ($ownerSignature !== current_signature() && !is_admin()) return '';
    $directOp = match ($deleteName) {
        'delete_thread' => 'delete_forum_thread',
        'delete_post' => 'delete_blog_post',
        default => $deleteName,
    };
    return "<div class='actions'><a class='button secondary' href='" . e($editUrl) . "'>Bearbeiten</a><form method='post' data-direct-op='" . e($directOp) . "' onsubmit=\"return confirm('Wirklich löschen?')\"><input type='hidden' name='signature' value='" . e($signature) . "'><button name='" . e($deleteName) . "' class='danger'>Löschen</button></form></div>";
}
