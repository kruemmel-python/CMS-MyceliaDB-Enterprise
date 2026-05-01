<?php
require_once __DIR__ . '/bootstrap.php';


if (!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])) {
    $op = strval($_POST['direct_op']);
    $response = call_mycelia_direct_ingest($op, strval($_POST['sealed_ingest']), direct_actor_context());
    if (($response['status'] ?? '') === 'ok' && $op === 'login_attractor') {
        $_SESSION['mycelia_signature'] = mycelia_identity($response['signature'] ?? '');
        $_SESSION['mycelia_username'] = mycelia_scalar_text($response['username'] ?? '');
        $_SESSION['mycelia_role'] = mycelia_scalar_text($response['role'] ?? (mycelia_scalar_text($response['username'] ?? '') === 'admin' ? 'admin' : 'user'));
        $_SESSION['mycelia_permissions'] = is_array($response['permissions'] ?? null) ? array_values(array_map('strval', $response['permissions'])) : [];
        redirect('profile.php');
    }
    if (($response['status'] ?? '') === 'ok' && $op === 'register_user') {
        flash('Registrierung erfolgreich. Der Nutzer wurde per Direct GPU Ingest als Mycelia-Nutrient-Node gespeichert.', 'info');
    } else {
        flash($response['message'] ?? 'Direct GPU Ingest fehlgeschlagen.', ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    }
    redirect('index.php');
}

if (isset($_POST['register'])) {
    $role = trim($_POST['user'] ?? '') === 'admin' ? 'admin' : 'user';
    $response = call_mycelia('register_user', [
        'username' => $_POST['user'] ?? '',
        'password' => $_POST['pass'] ?? '',
        'profile' => [
            'vorname' => $_POST['vorname'] ?? '',
            'nachname' => $_POST['nachname'] ?? '',
            'strasse' => $_POST['strasse'] ?? '',
            'hnr' => $_POST['hnr'] ?? '',
            'plz' => $_POST['plz'] ?? '',
            'ort' => $_POST['ort'] ?? '',
            'email' => $_POST['email'] ?? '',
            'role' => $role
        ]
    ]);
    flash(($response['status'] ?? '') === 'ok' ? 'Registrierung erfolgreich. Der Nutzer wurde als Mycelia-Nutrient-Node gespeichert.' : ($response['message'] ?? 'Registrierung fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('index.php');
}

if (isset($_POST['login'])) {
    $response = call_mycelia('login_attractor', [
        'username' => $_POST['user'] ?? '',
        'password' => $_POST['pass'] ?? ''
    ]);
    if (($response['status'] ?? '') === 'ok') {
        $_SESSION['mycelia_signature'] = mycelia_identity($response['signature'] ?? '');
        $_SESSION['mycelia_username'] = mycelia_scalar_text($response['username'] ?? '');
        $_SESSION['mycelia_role'] = mycelia_scalar_text($response['role'] ?? (mycelia_scalar_text($response['username'] ?? '') === 'admin' ? 'admin' : 'user'));
        $_SESSION['mycelia_permissions'] = is_array($response['permissions'] ?? null) ? array_values(array_map('strval', $response['permissions'])) : [];
        redirect('profile.php');
    }
    flash($response['message'] ?? 'Kein stabiler Auth-Attraktor gefunden.', 'error');
    redirect('index.php');
}

layout_header('Security Gate');
?>
<section class="hero">
    <div class="panel">
        <h1><?= e(txt('home.title')) ?></h1>
        <p class="muted"><?= e(txt('home.subtitle')) ?></p>
        <div class="kpi">
            <div><strong>0</strong><span>SQL-Tabellen</span></div>
            <div><strong>DAD</strong><span>Dynamic Associative Database</span></div>
            <div><strong>VRAM</strong><span>GPU-Crypto-Pfad, sofern verfügbar</span></div>
            <div><strong>V1</strong><span>Encrypted Snapshot Format</span></div>
        </div>
    </div>
    <div class="panel">
        <h2><?= e(txt('home.login_title')) ?></h2>
        <form method="post" data-direct-op="login_attractor">
            <label>Username</label><input name="username" required autocomplete="username">
            <label>Passwort</label><input name="password" type="password" required autocomplete="current-password">
            <button name="login">ATTRAKTOR PRÜFEN</button>
        </form>
    </div>
</section>

<section class="panel" style="margin-top:22px">
    <h2>Registrierung</h2>
    <form method="post" class="grid two" data-direct-op="register_user">
        <div>
            <label>Username</label><input name="username" required>
            <label>Passwort</label><input name="password" type="password" required>
            <label>Vorname</label><input name="vorname">
            <label>Nachname</label><input name="nachname">
        </div>
        <div>
            <label>Straße</label><input name="strasse">
            <label>Nr.</label><input name="hnr">
            <label>PLZ</label><input name="plz">
            <label>Ort</label><input name="ort">
            <label>E-Mail</label><input name="email" type="email">
            <button name="register">ALS NUTRIENT-NODE SPEICHERN</button>
            <p class="muted">Hinweis: Der Benutzername <b>admin</b> erhält Admin-Rechte für Forum und Blog.</p>
        </div>
    </form>
</section>
<?php layout_footer(); ?>
