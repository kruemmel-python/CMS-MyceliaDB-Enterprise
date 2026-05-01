<?php
require_once __DIR__ . '/bootstrap.php';
require_login();
$id = $_GET['id'] ?? $_POST['signature'] ?? '';

if (!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])) {
    $op = strval($_POST['direct_op']);
    $response = call_mycelia_direct_ingest($op, strval($_POST['sealed_ingest']), direct_actor_context());
    flash(($response['status'] ?? '') === 'ok' ? 'Direct GPU Ingest verarbeitet.' : ($response['message'] ?? 'Direct GPU Ingest fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    if ($op === 'delete_forum_thread') {
        redirect('forum.php');
    }
    $target = $_POST['signature'] ?? $_POST['target_signature'] ?? $id;
    redirect('thread.php?id=' . mycelia_url_component($target));
}

if (isset($_POST['update_thread'])) {
    $response = call_mycelia('update_forum_thread', array_merge(actor_payload(), [
        'signature' => $_POST['signature'] ?? '',
        'title' => $_POST['title'] ?? '',
        'body' => $_POST['body'] ?? ''
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Beitrag aktualisiert.' : ($response['message'] ?? 'Update fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('thread.php?id=' . mycelia_url_component($_POST['signature'] ?? ''));
}
if (isset($_POST['delete_thread'])) {
    $response = call_mycelia('delete_forum_thread', array_merge(actor_payload(), ['signature' => $_POST['signature'] ?? '']));
    flash(($response['status'] ?? '') === 'ok' ? 'Beitrag gelöscht.' : ($response['message'] ?? 'Löschen fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('forum.php');
}
if (isset($_POST['comment'])) {
    $response = call_mycelia('create_comment', array_merge(actor_payload(), [
        'target_signature' => $_POST['target_signature'] ?? '',
        'target_type' => 'forum_thread',
        'body' => $_POST['body'] ?? ''
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Kommentar gespeichert.' : ($response['message'] ?? 'Kommentar fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('thread.php?id=' . mycelia_url_component($_POST['target_signature'] ?? ''));
}
if (isset($_POST['delete_comment'])) {
    $response = call_mycelia('delete_comment', array_merge(actor_payload(), ['signature' => $_POST['comment_signature'] ?? '']));
    flash(($response['status'] ?? '') === 'ok' ? 'Kommentar gelöscht.' : ($response['message'] ?? 'Löschen fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('thread.php?id=' . mycelia_url_component($id));
}
if (isset($_POST['react_comment'])) {
    $response = call_mycelia('react_content', array_merge(actor_payload(), [
        'target_signature' => $_POST['comment_signature'] ?? '',
        'target_type' => 'comment',
        'reaction' => $_POST['react_comment']
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Kommentar-Reaktion gespeichert.' : ($response['message'] ?? 'Reaktion fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('thread.php?id=' . mycelia_url_component($id));
}

if (isset($_POST['react'])) {
    $response = call_mycelia('react_content', array_merge(actor_payload(), [
        'target_signature' => $_POST['target_signature'] ?? '',
        'target_type' => 'forum_thread',
        'reaction' => $_POST['react']
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Reaktion gespeichert.' : ($response['message'] ?? 'Reaktion fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('thread.php?id=' . mycelia_url_component($_POST['target_signature'] ?? ''));
}

$thread = require_mycelia_ok(call_mycelia('get_forum_thread', ['signature' => $id]))['thread'];
$comments = require_mycelia_ok(call_mycelia('list_comments', ['target_signature' => $id]))['comments'] ?? [];
$canEdit = ($thread['author_signature'] ?? '') === current_signature() || is_admin();
layout_header($thread['title'] ?? 'Thread');
?>
<section class="split">
    <article class="panel">
        <?php if ($canEdit && isset($_GET['edit'])): ?>
            <h1>Beitrag bearbeiten</h1>
            <form method="post" data-direct-op="update_forum_thread">
                <input type="hidden" name="signature" value="<?= e($thread['signature']) ?>">
                <label>Titel</label><input name="title" value="<?= e($thread['title']) ?>" required>
                <label>Beitrag</label><textarea name="body" required><?= e($thread['body']) ?></textarea>
                <?php media_upload_fields($thread['signature'], 'forum_thread'); ?>
                <button name="update_thread">Speichern</button>
            </form>
        <?php else: ?>
            <h1><?= e($thread['title']) ?></h1>
            <div class="meta"><span>von <?= e($thread['author_username']) ?></span><span><?= e(fmt_time($thread['created_at'])) ?></span><span>👍 <?= e($thread['likes']) ?></span><span>👎 <?= e($thread['dislikes']) ?></span></div>
            <div class="content"><?= e($thread['body']) ?></div>
            <?php render_media_gallery($thread['media'] ?? []); ?>
            <form method="post" class="actions" data-direct-op="react_content">
                <input type="hidden" name="target_signature" value="<?= e($thread['signature']) ?>">
                <button name="react" value="like" class="secondary">👍 Like</button>
                <button name="react" value="dislike" class="secondary">👎 Dislike</button>
            </form>
            <?= ownership_actions(mycelia_identity($thread['author_signature'] ?? ''), 'thread.php?id=' . mycelia_url_component($thread['signature'] ?? '') . '&edit=1', 'delete_thread', $thread['signature']) ?>
        <?php endif; ?>
    </article>
    <aside class="panel">
        <h2>Kommentieren</h2>
        <form method="post" data-direct-op="create_comment">
            <input type="hidden" name="target_signature" value="<?= e($thread['signature']) ?>">
            <textarea name="body" required></textarea>
            <button name="comment">Kommentar speichern</button>
        </form>
        <hr>
        <h2>Medium anhängen</h2>
        <form method="post" data-direct-op="upload_media">
            <?php media_upload_fields($thread['signature'], 'forum_thread'); ?>
            <button name="upload_media">Medium speichern</button>
        </form>
    </aside>
</section>
<section class="panel" style="margin-top:22px">
    <h2>Kommentare</h2>
    <?php foreach ($comments as $comment): ?>
        <article class="card">
            <div class="meta"><span><?= e($comment['author_username']) ?></span><span><?= e(fmt_time($comment['created_at'])) ?></span></div>
            <div class="content"><?= e($comment['body']) ?></div>
            <div class="meta"><span>👍 <?= e($comment['likes'] ?? 0) ?></span><span>👎 <?= e($comment['dislikes'] ?? 0) ?></span></div>
            <form method="post" class="actions" data-direct-op="react_content">
                <input type="hidden" name="comment_signature" value="<?= e($comment['signature']) ?>">
                <button name="react_comment" value="like" class="secondary">👍 Kommentar liken</button>
                <button name="react_comment" value="dislike" class="secondary">👎 Kommentar disliken</button>
            </form>
            <?php if (($comment['author_signature'] ?? '') === current_signature() || is_admin()): ?>
            <form method="post" class="actions" data-direct-op="delete_comment" onsubmit="return confirm('Kommentar löschen?')">
                <input type="hidden" name="comment_signature" value="<?= e($comment['signature']) ?>">
                <button name="delete_comment" class="danger">Kommentar löschen</button>
            </form>
            <?php endif; ?>
        </article>
    <?php endforeach; ?>
</section>
<?php layout_footer(); ?>
