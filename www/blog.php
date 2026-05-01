<?php
require_once __DIR__ . '/bootstrap.php';
require_login();

$blogId = $_GET['id'] ?? $_POST['blog_signature'] ?? '';
$postId = $_GET['post'] ?? $_POST['post_signature'] ?? '';

if (!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])) {
    $op = strval($_POST['direct_op']);
    $response = call_mycelia_direct_ingest($op, strval($_POST['sealed_ingest']), direct_actor_context());
    flash(($response['status'] ?? '') === 'ok' ? 'Direct GPU Ingest verarbeitet.' : ($response['message'] ?? 'Direct GPU Ingest fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('blog.php?id=' . mycelia_url_component($blogId) . ($postId ? '&post=' . mycelia_url_component($postId) : ''));
}

if (isset($_POST['comment_post'])) {
    $response = call_mycelia('create_comment', array_merge(actor_payload(), [
        'target_signature' => $_POST['post_signature'] ?? '',
        'target_type' => 'blog_post',
        'body' => $_POST['body'] ?? ''
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Kommentar gespeichert.' : ($response['message'] ?? 'Kommentar fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('blog.php?id=' . mycelia_url_component($blogId) . '&post=' . mycelia_url_component($_POST['post_signature'] ?? ''));
}
if (isset($_POST['react_post'])) {
    $response = call_mycelia('react_content', array_merge(actor_payload(), [
        'target_signature' => $_POST['post_signature'] ?? '',
        'target_type' => 'blog_post',
        'reaction' => $_POST['react_post']
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Reaktion gespeichert.' : ($response['message'] ?? 'Reaktion fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('blog.php?id=' . mycelia_url_component($blogId) . '&post=' . mycelia_url_component($_POST['post_signature'] ?? ''));
}
if (isset($_POST['react_comment'])) {
    call_mycelia('react_content', array_merge(actor_payload(), [
        'target_signature' => $_POST['comment_signature'] ?? '',
        'target_type' => 'comment',
        'reaction' => $_POST['react_comment']
    ]));
    redirect('blog.php?id=' . mycelia_url_component($blogId) . '&post=' . mycelia_url_component($postId));
}

if (isset($_POST['delete_comment'])) {
    call_mycelia('delete_comment', array_merge(actor_payload(), ['signature' => $_POST['comment_signature'] ?? '']));
    redirect('blog.php?id=' . mycelia_url_component($blogId) . '&post=' . mycelia_url_component($postId));
}

$blog = require_mycelia_ok(call_mycelia('get_blog', ['signature' => $blogId]))['blog'];
layout_header($blog['title'] ?? 'Blog');

if ($postId) {
    $post = require_mycelia_ok(call_mycelia('get_blog_post', ['signature' => $postId]))['post'];
    $comments = require_mycelia_ok(call_mycelia('list_comments', ['target_signature' => $postId]))['comments'] ?? [];
?>
<section class="panel">
    <p><a href="blog.php?id=<?= e($blogId) ?>">← Zurück zum Blog</a></p>
    <h1><?= e($post['title']) ?></h1>
    <div class="meta"><span>von <?= e($post['author_username']) ?></span><span><?= e(fmt_time($post['created_at'])) ?></span><span>👍 <?= e($post['likes']) ?></span><span>👎 <?= e($post['dislikes']) ?></span></div>
    <div class="content"><?= e($post['body']) ?></div>
    <?php render_media_gallery($post['media'] ?? []); ?>
    <form method="post" class="actions" data-direct-op="react_content">
        <input type="hidden" name="blog_signature" value="<?= e($blogId) ?>">
        <input type="hidden" name="post_signature" value="<?= e($postId) ?>">
        <button name="react_post" value="like" class="secondary">👍 Like</button>
        <button name="react_post" value="dislike" class="secondary">👎 Dislike</button>
    </form>
</section>
<section class="split" style="margin-top:22px">
    <div class="panel">
        <h2>Kommentare</h2>
        <?php foreach ($comments as $comment): ?>
            <article class="card">
                <div class="meta"><span><?= e($comment['author_username']) ?></span><span><?= e(fmt_time($comment['created_at'])) ?></span></div>
                <div class="content"><?= e($comment['body']) ?></div>
                <div class="meta"><span>👍 <?= e($comment['likes'] ?? 0) ?></span><span>👎 <?= e($comment['dislikes'] ?? 0) ?></span></div>
                <form method="post" class="actions" data-direct-op="react_content">
                    <input type="hidden" name="blog_signature" value="<?= e($blogId) ?>">
                    <input type="hidden" name="post_signature" value="<?= e($postId) ?>">
                    <input type="hidden" name="comment_signature" value="<?= e($comment['signature']) ?>">
                    <button name="react_comment" value="like" class="secondary">👍 Kommentar liken</button>
                    <button name="react_comment" value="dislike" class="secondary">👎 Kommentar disliken</button>
                </form>
                <?php if (($comment['author_signature'] ?? '') === current_signature() || is_admin()): ?>
                <form method="post" data-direct-op="delete_comment"><input type="hidden" name="blog_signature" value="<?= e($blogId) ?>"><input type="hidden" name="post_signature" value="<?= e($postId) ?>"><input type="hidden" name="comment_signature" value="<?= e($comment['signature']) ?>"><button name="delete_comment" class="danger">Löschen</button></form>
                <?php endif; ?>
            </article>
        <?php endforeach; ?>
    </div>
    <aside class="panel">
        <h2>Kommentieren</h2>
        <form method="post" data-direct-op="create_comment">
            <input type="hidden" name="blog_signature" value="<?= e($blogId) ?>">
            <input type="hidden" name="post_signature" value="<?= e($postId) ?>">
            <textarea name="body" required></textarea>
            <button name="comment_post">Kommentar speichern</button>
        </form>
        <?php if (($post['author_signature'] ?? '') === current_signature() || is_admin()): ?>
        <hr>
        <h2>Medium anhängen</h2>
        <form method="post" data-direct-op="upload_media">
            <input type="hidden" name="blog_signature" value="<?= e($blogId) ?>">
            <input type="hidden" name="post_signature" value="<?= e($postId) ?>">
            <?php media_upload_fields($postId, 'blog_post'); ?>
            <button name="upload_media">Medium speichern</button>
        </form>
        <?php endif; ?>
    </aside>
</section>
<?php
} else {
    $posts = require_mycelia_ok(call_mycelia('list_blog_posts', ['blog_signature' => $blogId]))['posts'] ?? [];
    $blogComments = require_mycelia_ok(call_mycelia('list_comments', ['target_signature' => $blogId]))['comments'] ?? [];
?>
<section class="panel">
    <h1><?= e($blog['title']) ?></h1>
    <p><?= e($blog['description']) ?></p>
    <div class="meta"><span>von <?= e($blog['owner_username']) ?></span><span>💬 <?= e($blog['comments'] ?? count($blogComments)) ?></span><span>👍 <?= e($blog['likes'] ?? 0) ?></span><span>👎 <?= e($blog['dislikes'] ?? 0) ?></span><span>🖼️ <?= e($blog['media_count'] ?? 0) ?></span><span>Stabilität <?= e($blog['stability']) ?></span></div>
    <?php render_media_gallery($blog['media'] ?? []); ?>
    <form method="post" class="actions" data-direct-op="react_content">
        <input type="hidden" name="blog_signature" value="<?= e($blogId) ?>">
        <input type="hidden" name="target_signature" value="<?= e($blogId) ?>">
        <input type="hidden" name="target_type" value="blog">
        <button name="reaction" value="like" class="secondary">👍 Blog liken</button>
        <button name="reaction" value="dislike" class="secondary">👎 Dislike</button>
    </form>
</section>
<section class="split" style="margin-top:22px">
    <div class="panel">
        <h2>Blog-Kommentare</h2>
        <?php foreach ($blogComments as $comment): ?>
            <article class="card">
                <div class="meta"><span><?= e($comment['author_username']) ?></span><span><?= e(fmt_time($comment['created_at'])) ?></span></div>
                <div class="content"><?= e($comment['body']) ?></div>
                <div class="meta"><span>👍 <?= e($comment['likes'] ?? 0) ?></span><span>👎 <?= e($comment['dislikes'] ?? 0) ?></span></div>
                <form method="post" class="actions" data-direct-op="react_content">
                    <input type="hidden" name="blog_signature" value="<?= e($blogId) ?>">
                    <input type="hidden" name="comment_signature" value="<?= e($comment['signature']) ?>">
                    <input type="hidden" name="target_type" value="comment">
                    <button name="reaction" value="like" class="secondary">👍 Kommentar liken</button>
                    <button name="reaction" value="dislike" class="secondary">👎 Kommentar disliken</button>
                </form>
                <?php if (($comment['author_signature'] ?? '') === current_signature() || is_admin()): ?>
                <form method="post" data-direct-op="delete_comment">
                    <input type="hidden" name="blog_signature" value="<?= e($blogId) ?>">
                    <input type="hidden" name="comment_signature" value="<?= e($comment['signature']) ?>">
                    <button name="delete_comment" class="danger">Löschen</button>
                </form>
                <?php endif; ?>
            </article>
        <?php endforeach; ?>
        <?php if (!$blogComments): ?><p class="muted">Noch keine Blog-Kommentare.</p><?php endif; ?>
    </div>
    <aside class="panel">
        <h2>Blog kommentieren</h2>
        <form method="post" data-direct-op="create_comment">
            <input type="hidden" name="blog_signature" value="<?= e($blogId) ?>">
            <input type="hidden" name="target_signature" value="<?= e($blogId) ?>">
            <input type="hidden" name="target_type" value="blog">
            <textarea name="body" required></textarea>
            <button name="comment_blog">Kommentar speichern</button>
        </form>
    </aside>
</section>
<section style="margin-top:22px">
<?php foreach ($posts as $post): ?>
    <article class="card">
        <h2><a href="blog.php?id=<?= e($blogId) ?>&post=<?= e($post['signature']) ?>"><?= e($post['title']) ?></a></h2>
        <div class="meta"><span><?= e(fmt_time($post['created_at'])) ?></span><span>👍 <?= e($post['likes']) ?></span><span>👎 <?= e($post['dislikes']) ?></span><span>💬 <?= e($post['comments']) ?></span><span>🖼️ <?= e($post['media_count'] ?? 0) ?></span></div>
        <?php render_media_gallery($post['media_preview'] ?? $post['media'] ?? []); ?>
    </article>
<?php endforeach; ?>
</section>
<?php } layout_footer(); ?>
