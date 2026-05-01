<?php
require_once __DIR__ . '/bootstrap.php';
require_login();
handle_direct_ingest('forum.php');

if (isset($_POST['create_thread'])) {
    $payload = array_merge(actor_payload(), [
        'title' => $_POST['title'] ?? '',
        'body' => $_POST['body'] ?? ''
    ]);
    $response = call_mycelia('create_forum_thread', $payload);
    flash(($response['status'] ?? '') === 'ok' ? 'Forenbeitrag gespeichert.' : ($response['message'] ?? 'Speichern fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('forum.php');
}
if (isset($_POST['delete_thread'])) {
    $response = call_mycelia('delete_forum_thread', array_merge(actor_payload(), ['signature' => $_POST['signature'] ?? '']));
    flash(($response['status'] ?? '') === 'ok' ? 'Forenbeitrag gelöscht.' : ($response['message'] ?? 'Löschen fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('forum.php');
}
$threads = require_mycelia_ok(call_mycelia('list_forum_threads', ['limit' => 200]))['threads'] ?? [];
layout_header(txt('forum.title'));
?>
<section class="split">
    <div>
        <h1><?= e(txt('forum.title')) ?></h1>
        <?php foreach ($threads as $thread): ?>
            <article class="card">
                <h2><a href="thread.php?id=<?= e($thread['signature']) ?>"><?= e($thread['title']) ?></a></h2>
                <div class="meta">
                    <span>von <?= e($thread['author_username']) ?></span>
                    <span><?= e(fmt_time($thread['created_at'] ?? null)) ?></span>
                    <span>👍 <?= e($thread['likes'] ?? 0) ?></span>
                    <span>👎 <?= e($thread['dislikes'] ?? 0) ?></span>
                    <span>💬 <?= e($thread['comments'] ?? 0) ?></span><span>🖼️ <?= e($thread['media_count'] ?? 0) ?></span>
                    <span>Stabilität <?= e($thread['stability'] ?? 'n/a') ?></span>
                </div>
                <?php render_media_gallery($thread['media_preview'] ?? $thread['media'] ?? []); ?>
                <?= ownership_actions(mycelia_identity($thread['author_signature'] ?? ''), 'thread.php?id=' . mycelia_url_component($thread['signature'] ?? '') . '&edit=1', 'delete_thread', $thread['signature']) ?>
            </article>
        <?php endforeach; ?>
        <?php if (!$threads): ?><p class="muted"><?= e(txt('forum.empty')) ?></p><?php endif; ?>
    </div>
    <aside class="panel">
        <h2><?= e(txt('forum.new_thread')) ?></h2>
        <form method="post" data-direct-op="create_forum_thread">
            <label>Titel</label><input name="title" required maxlength="240">
            <label>Beitrag</label><textarea name="body" required></textarea>
            <?php media_upload_fields('', 'forum_thread'); ?>
            <button name="create_thread"><?= e(txt('forum.save_button')) ?></button>
        </form>
    </aside>
</section>
<?php layout_footer(); ?>
