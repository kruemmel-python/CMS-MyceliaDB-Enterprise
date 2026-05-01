<?php
require_once __DIR__ . '/bootstrap.php';
require_login();

if (!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])) {
    $response = call_mycelia_direct_ingest(strval($_POST['direct_op']), strval($_POST['sealed_ingest']), direct_actor_context());
    flash(($response['status'] ?? '') === 'ok' ? 'Reaktion gespeichert.' : ($response['message'] ?? 'Reaktion fehlgeschlagen.'), ($response['status'] ?? '') === 'ok' ? 'info' : 'error');
    redirect('blogs.php');
}

$blogs = require_mycelia_ok(call_mycelia('list_blogs', []))['blogs'] ?? [];
layout_header(txt('blogs.title'));
?>
<section class="panel">
    <h1><?= e(txt('blogs.title')) ?></h1>
    <p class="muted"><?= e(txt('blogs.subtitle')) ?></p>
</section>
<section class="grid">
<?php foreach ($blogs as $blog): ?>
    <article class="card">
        <h2><a href="blog.php?id=<?= e($blog['signature']) ?>"><?= e($blog['title']) ?></a> <?php render_blog_theme_badge($blog); ?></h2>
        <p><?= e($blog['description']) ?></p>
        <div class="meta"><span>von <?= e($blog['owner_username']) ?></span><span><?= e($blog['posts']) ?> Beiträge</span><span>💬 <?= e($blog['comments'] ?? 0) ?></span><span>🖼️ <?= e($blog['media_count'] ?? 0) ?></span><span><?= e(fmt_time($blog['updated_at'])) ?></span></div>
        <?php render_reaction_summary($blog); ?>
        <?php render_media_gallery($blog['media_preview'] ?? $blog['media'] ?? []); ?>
        <?php render_reaction_sticker_form($blog['signature'] ?? '', 'blog'); ?>
    </article>
<?php endforeach; ?>
</section>
<?php if (!$blogs): ?><p class="muted"><?= e(txt('blogs.empty')) ?></p><?php endif; ?>
<?php layout_footer(); ?>
