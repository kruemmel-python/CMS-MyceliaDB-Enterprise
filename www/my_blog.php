<?php
require_once __DIR__ . '/bootstrap.php';
require_login();
if (!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])) {
    $response = call_mycelia_direct_ingest(strval($_POST['direct_op']), strval($_POST['sealed_ingest']), direct_actor_context());
    flash(($response['status'] ?? '') === 'ok' ? 'Direct GPU Ingest verarbeitet.' : ($response['message'] ?? 'Direct GPU Ingest fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('my_blog.php' . (!empty($_GET['blog']) ? '?blog=' . mycelia_url_component($_GET['blog'] ?? '') : ''));
}

if (isset($_POST['create_blog'])) {
    $response = call_mycelia('create_blog', array_merge(actor_payload(), [
        'title' => $_POST['title'] ?? '',
        'description' => $_POST['description'] ?? ''
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Blog erstellt.' : ($response['message'] ?? 'Blog konnte nicht erstellt werden.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('my_blog.php');
}
if (isset($_POST['update_blog'])) {
    $response = call_mycelia('update_blog', array_merge(actor_payload(), [
        'signature' => $_POST['blog_signature'] ?? '',
        'title' => $_POST['title'] ?? '',
        'description' => $_POST['description'] ?? ''
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Blog aktualisiert.' : ($response['message'] ?? 'Update fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('my_blog.php?blog=' . mycelia_url_component($_POST['blog_signature'] ?? ''));
}
if (isset($_POST['delete_blog'])) {
    $response = call_mycelia('delete_blog', array_merge(actor_payload(), ['signature' => $_POST['blog_signature'] ?? '']));
    flash(($response['status'] ?? '') === 'ok' ? 'Blog gelöscht.' : ($response['message'] ?? 'Löschen fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('my_blog.php');
}
if (isset($_POST['create_post'])) {
    $response = call_mycelia('create_blog_post', array_merge(actor_payload(), [
        'blog_signature' => $_POST['blog_signature'] ?? '',
        'title' => $_POST['title'] ?? '',
        'body' => $_POST['body'] ?? '',
        'publish_status' => $_POST['publish_status'] ?? 'published'
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Blog-Beitrag gespeichert.' : ($response['message'] ?? 'Beitrag fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('my_blog.php?blog=' . mycelia_url_component($_POST['blog_signature'] ?? ''));
}
if (isset($_POST['update_post'])) {
    $response = call_mycelia('update_blog_post', array_merge(actor_payload(), [
        'signature' => $_POST['post_signature'] ?? '',
        'title' => $_POST['title'] ?? '',
        'body' => $_POST['body'] ?? '',
        'publish_status' => $_POST['publish_status'] ?? 'published'
    ]));
    flash(($response['status'] ?? '') === 'ok' ? 'Beitrag aktualisiert.' : ($response['message'] ?? 'Update fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('my_blog.php?blog=' . mycelia_url_component($_POST['blog_signature'] ?? ''));
}
if (isset($_POST['delete_post'])) {
    $response = call_mycelia('delete_blog_post', array_merge(actor_payload(), ['signature' => $_POST['post_signature'] ?? '']));
    flash(($response['status'] ?? '') === 'ok' ? 'Beitrag gelöscht.' : ($response['message'] ?? 'Löschen fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('my_blog.php?blog=' . mycelia_url_component($_POST['blog_signature'] ?? ''));
}

$blogs = require_mycelia_ok(call_mycelia('list_blogs', ['owner_signature' => current_signature()]))['blogs'] ?? [];
$selectedBlogId = $_GET['blog'] ?? ($blogs[0]['signature'] ?? '');
$selectedBlog = null;
$posts = [];
if ($selectedBlogId) {
    $selectedBlogResponse = call_mycelia('get_blog', ['signature' => $selectedBlogId]);
    if (($selectedBlogResponse['status'] ?? '') === 'ok') {
        $selectedBlog = $selectedBlogResponse['blog'];
        $posts = require_mycelia_ok(call_mycelia('list_blog_posts', ['blog_signature' => $selectedBlogId]))['posts'] ?? [];
    }
}
$editPost = null;
if (!empty($_GET['edit_post'])) {
    $postResponse = call_mycelia('get_blog_post', ['signature' => $_GET['edit_post']]);
    if (($postResponse['status'] ?? '') === 'ok') $editPost = $postResponse['post'];
}
layout_header(txt('my_blog.title'));
?>
<section class="split">
    <div>
        <section class="panel">
            <h1>Mein Blog-Cockpit</h1>
            <?php if ($blogs): ?>
            <div class="actions">
                <?php foreach ($blogs as $blog): ?><a class="button secondary" href="my_blog.php?blog=<?= e($blog['signature']) ?>"><?= e($blog['title']) ?></a><?php endforeach; ?>
            </div>
            <?php endif; ?>
        </section>

        <?php if ($selectedBlog): ?>
        <section class="panel" style="margin-top:22px">
            <h2>Blog bearbeiten</h2>
            <form method="post" data-direct-op="update_blog">
                <input type="hidden" name="blog_signature" value="<?= e($selectedBlog['signature']) ?>">
                <label>Titel</label><input name="title" value="<?= e($selectedBlog['title']) ?>" required>
                <label>Beschreibung</label><textarea name="description"><?= e($selectedBlog['description']) ?></textarea>
                <?php render_media_gallery($selectedBlog['media'] ?? []); ?>
                <?php media_upload_fields($selectedBlog['signature'] ?? '', 'blog'); ?>
                <div class="actions"><button name="update_blog">Blog speichern</button><button name="delete_blog" data-direct-op="delete_blog" class="danger" onclick="return confirm('Blog löschen?')">Blog löschen</button></div>
            </form>
        </section>

        <section class="panel" style="margin-top:22px">
            <h2><?= $editPost ? 'Beitrag bearbeiten' : 'Neuer Beitrag' ?></h2>
            <form method="post" data-direct-op="<?= $editPost ? 'update_blog_post' : 'create_blog_post' ?>">
                <input type="hidden" name="blog_signature" value="<?= e($selectedBlog['signature']) ?>">
                <?php if ($editPost): ?><input type="hidden" name="post_signature" value="<?= e($editPost['signature']) ?>"><?php endif; ?>
                <label>Titel</label><input name="title" value="<?= e($editPost['title'] ?? '') ?>" required>
                <label>Status</label><select name="publish_status"><option value="published">published</option><option value="draft" <?= (($editPost['publish_status'] ?? '') === 'draft') ? 'selected' : '' ?>>draft</option></select>
                <label>Inhalt</label><textarea name="body" required><?= e($editPost['body'] ?? '') ?></textarea>
                <?php media_upload_fields($editPost['signature'] ?? '', 'blog_post'); ?>
                <button name="<?= $editPost ? 'update_post' : 'create_post' ?>"><?= $editPost ? 'Beitrag speichern' : 'Beitrag erstellen' ?></button>
            </form>
        </section>

        <section style="margin-top:22px">
            <?php foreach ($posts as $post): ?>
            <article class="card">
                <h2><?= e($post['title']) ?></h2>
                <div class="meta"><span><?= e($post['publish_status']) ?></span><span><?= e(fmt_time($post['updated_at'])) ?></span><span>👍 <?= e($post['likes']) ?></span><span>💬 <?= e($post['comments']) ?></span><span>🖼️ <?= e($post['media_count'] ?? 0) ?></span></div>
                <?php render_media_gallery($post['media_preview'] ?? $post['media'] ?? []); ?>
                <div class="actions">
                    <a class="button secondary" href="blog.php?id=<?= e($selectedBlog['signature']) ?>&post=<?= e($post['signature']) ?>">Ansehen</a>
                    <a class="button secondary" href="my_blog.php?blog=<?= e($selectedBlog['signature']) ?>&edit_post=<?= e($post['signature']) ?>">Bearbeiten</a>
                    <form method="post" data-direct-op="delete_blog_post" onsubmit="return confirm('Beitrag löschen?')"><input type="hidden" name="blog_signature" value="<?= e($selectedBlog['signature']) ?>"><input type="hidden" name="post_signature" value="<?= e($post['signature']) ?>"><button name="delete_post" class="danger">Löschen</button></form>
                </div>
            </article>
            <?php endforeach; ?>
        </section>
        <?php endif; ?>
    </div>
    <aside class="panel">
        <h2>Neuen Blog erstellen</h2>
        <form method="post" data-direct-op="create_blog">
            <label>Titel</label><input name="title" required>
            <label>Beschreibung</label><textarea name="description"></textarea>
            <?php media_upload_fields('', 'blog'); ?>
            <button name="create_blog">Blog als Attraktor speichern</button>
        </form>
    </aside>
</section>
<?php layout_footer(); ?>
