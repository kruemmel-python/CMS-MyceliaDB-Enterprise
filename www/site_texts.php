<?php
/**
 * MyceliaDB Enterprise CMS text registry.
 * Every visible website string that should be editable in the Admin panel is
 * declared here with a stable key. Overrides are stored in MyceliaDB, not PHP.
 */
const MYCELIA_SITE_TEXT_DEFAULTS = [
    'nav.profile' => 'Profil',
    'nav.forum' => 'Forum',
    'nav.blogs' => 'Blogs',
    'nav.my_blog' => 'Mein Blog',
    'nav.admin' => 'Admin',
    'nav.plugins' => 'Plugins',
    'nav.logout' => 'Logout',
    'nav.login' => 'Login',
    'nav.privacy' => 'Datenschutz',
    'brand.name' => 'MYCELIADB',
    'footer.text' => 'SQL-freie Enterprise-Webplattform · Direct GPU Ingest Phase 1 · PHP-blinde Formulare · Python/OpenCL Mycelia Engine · Autosnapshot-Persistenz',

    'home.title' => 'MyceliaDB Enterprise Portal',
    'home.subtitle' => 'Autarke Web-Plattform ohne MySQL: Registrierung, Profil, Forum, Kommentare, Reaktionen, Blogs und Admin-Verwaltung werden als verschlüsselte Attraktoren in der MyceliaDB gespeichert und per Autosnapshot wiederhergestellt.',
    'home.login_title' => 'Login via Auth-Attraktor',
    'home.register_title' => 'Registrierung als Nutrient-Node',
    'home.login_button' => 'Einloggen',
    'home.register_button' => 'Registrieren',

    'profile.title' => 'Profil',
    'profile.welcome' => 'Willkommen',
    'profile.actions' => 'Aktionen',
    'profile.open_forum' => 'Forum öffnen',
    'profile.manage_blog' => 'Eigenen Blog verwalten',
    'profile.admin_console' => 'Admin-Konsole',
    'profile.privacy_center' => 'Datenschutz & Datenexport',
    'profile.update_button' => 'UPDATE MYCELIA PROFILE',

    'privacy.title' => 'Datenschutz-Center',
    'privacy.subtitle' => 'Lade deine gespeicherten personenbezogenen Daten als maschinenlesbares JSON herunter oder lösche deinen Account vollständig aus der MyceliaDB.',
    'privacy.export_title' => 'Daten herunterladen',
    'privacy.export_body' => 'Der Export enthält Profil, eigene Forenbeiträge, Kommentare, Reaktionen, Blogs und Blogposts. Credential-Secrets wie Passwort oder Auth-Pattern werden nicht exportiert.',
    'privacy.export_button' => 'Meine Daten als JSON herunterladen',
    'privacy.delete_title' => 'Account löschen',
    'privacy.delete_body' => 'Diese Aktion löscht deinen User-Attraktor und zugeordnete personenbezogene Inhaltsknoten aus dem aktiven Mycelia-Graphen und schreibt anschließend den Autosnapshot neu.',
    'privacy.delete_confirm_label' => 'Zur Bestätigung DELETE eingeben',
    'privacy.password_label' => 'Aktuelles Passwort',
    'privacy.delete_button' => 'Account endgültig löschen',
    'privacy.warning' => 'Hinweis: Der Datenexport materialisiert deine eigenen Daten zwangsläufig für den Download im Browser. Für maximale VRAM-Residency werden Daten ansonsten nicht unnötig in PHP interpretiert.',


    'forum.title' => 'Forum',
    'forum.new_thread' => 'Neuer Beitrag',
    'forum.empty' => 'Noch keine Forenbeiträge.',
    'forum.save_button' => 'Im Myzel speichern',

    'blogs.title' => 'Blogs',
    'blogs.subtitle' => 'Jeder Blog ist ein eigener Mycelia-Attraktor. Beiträge und Kommentare werden verschlüsselt im Autosnapshot persistiert.',
    'blogs.empty' => 'Noch keine Blogs. Erstelle deinen ersten Blog unter „Mein Blog“.',

    'my_blog.title' => 'Mein Blog',
    'my_blog.create_blog' => 'Blog erstellen',
    'my_blog.create_post' => 'Blog-Beitrag erstellen',

    'admin.title' => 'Admin-Konsole',
    'admin.subtitle' => 'Enterprise-Verwaltung für Inhalte, Webseitentexte und Benutzerrechte. PHP bleibt Zero-Logic-Gateway; alle Änderungen werden durch die Mycelia Engine autorisiert.',
    'admin.texts_title' => 'Webseitentexte verwalten',
    'admin.users_title' => 'Benutzerrechte verwalten',
    'admin.save_text' => 'Text speichern',
    'admin.save_rights' => 'Rechte speichern',
    'admin.vram_title' => 'VRAM-Residency-Audit',
    'plugins.title' => 'Mycelia Plugin-Attraktoren',
    'plugins.subtitle' => 'Installiere signierte deklarative Plugin-Manifeste ohne PHP/Python-Codeausführung. Plugins erhalten nur explizite Capabilities und liefern ausschließlich Safe-Aggregate.',
    'plugins.install_title' => 'Plugin-Manifest installieren',
    'plugins.manifest_label' => 'Manifest JSON',
    'plugins.install_button' => 'Plugin-Attraktor installieren',
    'plugins.installed_title' => 'Installierte Plugins',
    'plugins.run_button' => 'Ausführen',
    'plugins.enable_button' => 'Aktivieren',
    'plugins.disable_button' => 'Deaktivieren',
    'plugins.delete_button' => 'Löschen',
    'plugins.catalog_title' => 'Capability-Katalog',

    'admin.forum_title' => 'Forum',
    'admin.blogs_title' => 'Blogs',
    'admin.blogposts_title' => 'Blogposts',
    'admin.comments_title' => 'Kommentare',
];
?>