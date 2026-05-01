# MyceliaDB Enterprise WWW

> Hinweis zu Sicherheitsformulierungen: Diese Dokumentation beschreibt die implementierten Schutzmechanismen und prüfbaren Evidenzpfade. Es wird keine prozentuale Sicherheitsfestlegung verwendet. Entscheidend sind die konkret umgesetzten Mechanismen: Zero-Logic-Gateway, Direct-Ingest, Native-VRAM-Pfade, Session-/Tokenbindung, Log-Redaction, Snapshot-Verschlüsselung, E2EE-Mailbox und prüfbare Auditberichte.


Diese Version ergänzt einen neuen Ordner `www/` als vollständiges Enterprise-Webfrontend.

## Start

Terminal 1:

```powershell
cd D:\myceliadb_autarkic_platform\html
python mycelia_platform.py
```

Terminal 2:

```powershell
cd D:\myceliadb_autarkic_platform\www
php -S 127.0.0.1:8090
```

Browser:

```text
http://127.0.0.1:8090/index.php
```

## Funktionen

- Registrierung und Login über Mycelia Auth-Attraktoren
- Profilansicht und Profilbearbeitung
- Forum:
  - Beiträge erstellen, ändern, löschen
  - Kommentare erstellen und löschen
  - Likes/Dislikes auf Beiträge und Kommentare
- Blog:
  - Jeder Nutzer kann eigene Blogs erstellen
  - Blogposts erstellen, ändern, löschen
  - Kommentare und Likes/Dislikes
- Admin:
  - Nutzer `admin` erhält Admin-Rolle
  - Moderation von Forum, Blogs, Posts und Kommentaren

## Persistenz

Alle neuen Entitäten werden als Mycelia/DAD-Attraktoren gespeichert:

- `mycelia_forum_threads`
- `mycelia_comments`
- `mycelia_reactions`
- `mycelia_blogs`
- `mycelia_blog_posts`

Die Inhalte werden über die Engine verschlüsselt und über `html/snapshots/autosave.mycelia` automatisch persistiert.
Es wird keine SQL-Datenbank erzeugt oder benötigt.


## Direct GPU Ingest Phase 1

Ab Version 1.7 versiegelt das `www/`-Frontend sensitive Formularinhalte im Browser, bevor PHP sie empfängt.

Ablauf:

1. `www/assets/direct-ingest.js` ruft `www/ingest_manifest.php` auf.
2. `ingest_manifest.php` fragt die Engine per `direct_ingest_manifest` nach dem öffentlichen RSA-OAEP-Schlüssel.
3. Der Browser erzeugt pro Submit einen AES-256-GCM-Schlüssel und verschlüsselt die Formularfelder.
4. Der AES-Schlüssel wird mit RSA-OAEP-3072-SHA256 versiegelt.
5. PHP erhält nur noch:
   - `direct_op`
   - `sealed_ingest`
6. PHP leitet das Paket unverändert an `mycelia_platform.py` weiter.
7. Die Engine öffnet das Paket, normalisiert die Payload und speichert sie als Mycelia-Attraktor.

Wichtig: Dies ist **Phase 1: PHP-blinder Direct Ingest**. Damit werden Klartextfelder aus PHP-POST, PHP-Formularlogik und PHP-Logs herausgehalten. Es ist noch kein vollständiger Beweis für CPU-RAM-freie VRAM-Residency, weil die Python-Engine den Envelope derzeit mit `cryptography` in CPU-RAM öffnet, bevor die Daten in die Mycelia/GPU-Crypto-Schicht übergehen.

Neue Engine-Befehle:

- `direct_ingest_manifest`
- `direct_ingest`

Neue Dateien:

- `www/assets/direct-ingest.js`
- `www/ingest_manifest.php`
- `tests/test_direct_gpu_ingest.py`

Neue Residency-Felder:

```json
{
  "direct_gpu_ingest": true,
  "direct_ingest_phase": "phase1_php_blind",
  "php_blind_form_transport": true,
  "python_cpu_decrypt_materialized": true,
  "strict_inflight_vram_claim": false
}
```

Der nächste harte Schritt bleibt ein nativer GPU-Envelope-Opener, damit das AES-GCM-Öffnen und die erste JSON-/Payload-Verarbeitung nicht mehr in Python-CPU-Speicher materialisiert werden.


## Version 1.9: Zero-Logic Gateway / Engine Session Binding

Start wie bisher:

```powershell
cd D:\myceliadb_autarkic_platform\html
python mycelia_platform.py
```

Zweites Terminal:

```powershell
cd D:\myceliadb_autarkic_platform\www
php -S 127.0.0.1:8090
```

Neue Sicherheitsregeln:

- Produktive POST-Requests müssen `sealed_ingest` + `direct_op` enthalten.
- PHP blockiert Klartext-POSTs mit HTTP 400.
- PHP speichert nur ein opaques Engine-Session-Handle und ein rotierendes Request-Token.
- Das Request-Token wird von `direct-ingest.js` in den WebCrypto-Envelope eingeschlossen.
- Die Engine prüft und rotiert das Token bei jeder geschützten Mutation.
- Rollen, Autor, Owner und Signaturen werden von der Engine injiziert, nicht von PHP entschieden.

Tests:

```powershell
cd D:\myceliadb_autarkic_platform
python -m unittest discover -s tests -v
```


## v1.10 Native-GPU-Residency-Contract

Neue Audit-/Zertifizierungsbefehle der Engine:

- `native_gpu_capability_report`
- `native_gpu_residency_selftest`
- `strict_vram_certification`

Neues Werkzeug:

```powershell
python tools\mycelia_strict_vram_certify.py --engine http://127.0.0.1:9999 --json-out strict_cert.json
```

Mit externem Memory-Probe-Report:

```powershell
python tools\mycelia_strict_vram_certify.py --engine http://127.0.0.1:9999 --probe-report residency_probe.json --json-out strict_cert.json
```

Die Zertifizierung ist fail-closed: Ohne native Bibliothek mit den erwarteten Exports bleibt die Strict-VRAM-Zertifizierung fail-closed blockiert.


## v1.12 Session Token Broker

Diese Version behebt Token-Drift beim Wechsel zwischen Profil, Forum, Blog und Admin:

- frischer `direct_ingest_manifest` pro Formular-Submit,
- Engine-seitiger One-Time-Token-Pool,
- kein Browser-Manifest-Cache,
- keine Überschreibung von Zielsignaturen durch `actor_signature`,
- Regressionstest für alle Web-Aktionen: `tests/test_web_action_token_integrity.py`.


## Version 1.13 Admin CMS und Rechteverwaltung

Das Admin-Panel enthält jetzt zusätzlich:

- Webseitentexte bearbeiten: Speicherung in `mycelia_site_texts`
- Benutzerrechte vergeben und entziehen
- Rollen `user`, `moderator`, `admin`
- Rechtekatalog aus der Mycelia Engine
- Rechteänderungen wirken sofort auf bestehende Engine-Sessions
- alle Admin-Mutationen laufen über Direct GPU Ingest

Start unverändert:

```powershell
cd D:\myceliadb_autarkic_platform\html
python mycelia_platform.py
```

```powershell
cd D:\myceliadb_autarkic_platform\www
php -S 127.0.0.1:8090
```


## Version 1.19 Plugin Attractor System

Neues Admin-Plugin-System:

```text
www/plugins.php
```

Eigenschaften:

- keine PHP-/Python-Code-Plugins
- nur deklarative JSON-Manifeste
- Capability-Sandbox
- kein Netzwerk-/Dateisystem-/Socket-Zugriff
- nur Safe-Aggregate, keine Rohdaten
- Observer-Tension mit automatischer Suspendierung
- Plugin-Manifeste werden verschlüsselt in `mycelia_plugins` gespeichert
- Plugin-Audits werden in `mycelia_plugin_audit` gespeichert

Beispielmanifest:

```json
{
  "plugin_id": "anonymous_stats",
  "name": "Anonyme Statistiken",
  "version": "1.0.0",
  "description": "Zeigt nur aggregierte Zähler ohne Rohdatenzugriff.",
  "hooks": ["admin.dashboard"],
  "capabilities": ["stats.forum.count", "stats.blog_post.count", "stats.user.count"],
  "constraints": {"max_records": 10000, "tension_threshold": 0.72},
  "outputs": [{"key": "summary", "type": "metric_cards"}]
}
```

Tests:

```powershell
python -m unittest discover -s tests -v
```


## v1.19.2 DLL Recognition Hotfix

Nach dem Build:

```powershell
cd D:\web_sicherheit\html\native
.\build_native_gpu_envelope.ps1 -Clean
cd D:\web_sicherheit\html
python mycelia_platform.py
```

Erwartet wird nun eine Meldung ähnlich:

```text
Native GPU Residency DLL geladen: D:\web_sicherheit\html\native\mycelia_gpu_envelope.dll
```

Optional kann der Pfad explizit gesetzt werden:

```powershell
$env:MYCELIA_GPU_ENVELOPE_LIBRARY="D:\web_sicherheit\html\native\mycelia_gpu_envelope.dll"
python mycelia_platform.py
```


## v1.19.5 Admin-/Console-Parität für VRAM-Evidence

Das Admin-Panel besitzt jetzt den Button **Konsole/UI synchronisieren**. Dieser ruft den neuen Engine-Befehl `strict_vram_evidence_bundle` auf und zeigt Manifest-/Probe-/Native-/Strict-Zertifizierungsdaten aus einem konsistenten Snapshot an.

Nach dem Einreichen von `residency_probe.json` im Admin-Panel wird automatisch:

1. `submit_external_memory_probe`
2. `native_gpu_capability_report`
3. `strict_vram_certification`
4. `strict_vram_evidence_bundle`

ausgeführt.

Wenn `strict_vram_certification_enabled=false` angezeigt wird, Engine neu starten mit:

```powershell
$env:MYCELIA_STRICT_VRAM_CERTIFICATION="1"
python .\mycelia_platform.py
```


## v1.19.7 Classified Memory Probe

Neue RAM-Probe-Nutzung:

```powershell
python D:\web_sicherheit\tools\mycelia_memory_probe.py --pid <PID> --challenge-id <CHALLENGE> --probe-sensitive "Leipzig" --probe-sensitive "Krümmel" --probe-public "4166bbf4b6c623571001321d8721b576d023c9f2299624370d2e12d1df56caf9" --json-out D:\web_sicherheit\residency_probe.json
```

`--probe` bleibt verfügbar. 64-hex-Probes werden automatisch als `public_identifier` klassifiziert.
Für harte Zertifizierung zählen nur `strict_hits`; öffentliche Signaturtreffer werden weiterhin reported, blockieren aber nicht.


## Version 1.19.9 Scheduled Heartbeat Audit

Manueller Einmallauf:

```powershell
cd D:\web_sicherheit
powershell -ExecutionPolicy Bypass -File .\tools\run_heartbeat_audit.ps1 -ProjectRoot D:\web_sicherheit -Engine http://127.0.0.1:9999/
```

Windows Scheduled Task installieren:

```powershell
cd D:\web_sicherheit
powershell -ExecutionPolicy Bypass -File .\tools\install_heartbeat_audit_task.ps1 -ProjectRoot D:\web_sicherheit -Engine http://127.0.0.1:9999/ -At 03:15
```

Die Engine muss im Strict-Modus laufen:

```powershell
cd D:\web_sicherheit\html
$env:MYCELIA_STRICT_VRAM_CERTIFICATION="1"
$env:MYCELIA_STRICT_RESPONSE_REDACTION="1"
$env:MYCELIA_AUTORESTORE="0"
python mycelia_platform.py
```

Das Admin-Dashboard zeigt danach den signierten Status unter `Scheduled Heartbeat Audit`.


---

## v1.19.10 PHP Safe Rendering Hotfix

Die PHP-Render-Hilfsfunktion `e()` wurde gehärtet. Engine-Antworten können im Strict-VRAM-Modus strukturierte Safe-Fragments oder Redaction-Objekte liefern, zum Beispiel `{"text":"[redacted:strict-vram]"}`. Bisher führte ein direktes `strval(array)` in `bootstrap.php` zu `Warning: Array to string conversion` und zur Anzeige von `Array` in Forum/Blog/Admin.

Neu:

- `mycelia_scalar_text()` normalisiert Arrays, Safe-Fragments und Redaction-Objekte kontrolliert.
- `e()` ruft kein `strval(array)` mehr auf.
- `ui_excerpt()` ist ebenfalls array-sicher.
- Strukturierte Arrays werden als `[structured-data]` gerendert, sofern sie nicht explizit ein `text`, `value` oder `message`-Feld enthalten.
- Neuer Test: `tests/test_php_safe_rendering.py`.



---

## v1.21.25 Media-Attractor-System für Forum, Blog und Blog-Erstellung

Diese Version ergänzt die Weboberfläche um einen durchgängigen Media-Pfad. Bilder und sichere Medienlinks sind nicht mehr nur an Forum-Threads oder Blogposts möglich, sondern auch direkt an Blogs.

### Neue Nutzerfunktionen

- Forum:
  - Bild oder Medienlink an Thread anhängen
  - Medienvorschau in der Forenliste
  - Mediengalerie auf der Thread-Seite
- Blogs:
  - Bild oder Medienlink beim Erstellen eines Blogs anhängen
  - Bild oder Medienlink beim Bearbeiten eines Blogs ergänzen
  - Medienvorschau in `blogs.php`
  - Medienanzeige in `blog.php`
  - Medienanzeige und Upload in `my_blog.php`
- Blogposts:
  - Bild oder Medienlink beim Erstellen anhängen
  - Bild oder Medienlink beim Bearbeiten ergänzen
  - Medienvorschau und Mediengalerie

### Neue/erweiterte Persistenz

Medien werden als eigene Attraktoren gespeichert:

```text
mycelia_media_nodes
```

Zusätzlich zu den bisherigen Content-Tabellen:

```text
mycelia_forum_threads
mycelia_comments
mycelia_reactions
mycelia_blogs
mycelia_blog_posts
mycelia_media_nodes
```

### Direct GPU Ingest und Medien

Das Browser-Skript `www/assets/direct-ingest.js` liest Datei-Uploads als Base64 und versiegelt sie gemeinsam mit dem Formularinhalt.

Die Engine erhält und normalisiert jetzt Media-Felder für:

```text
create_forum_thread
update_forum_thread
create_blog
update_blog
create_blog_post
update_blog_post
```

Wichtig: Ältere fehlerhafte Uploadversuche erzeugten keinen Media-Node. Nach dem Update müssen Bilder oder Links erneut gespeichert werden.

### Unterstützte Medien

Uploads:

```text
JPEG, PNG, GIF, WebP
max. 3 MB
```

Sichere Links:

```text
YouTube
Vimeo
HTTPS-Bilder
```

### Diagnose

Wenn keine Medien sichtbar sind, Engine-Log prüfen:

```text
query_sql_like: Tabelle=mycelia_media_nodes ... Treffer=0
```

`Treffer=0` bedeutet, dass kein Medium gespeichert wurde. Dann beide Server neu starten, Browser per `Strg + F5` hart aktualisieren und das Medium erneut anhängen.

### Tests

```powershell
cd D:\web_sicherheit
python -m unittest tests.test_media_attractor_system -v
```

Dokumentierter Fixstand:

```text
Ran 8 tests in 2.146s
OK
```


## v1.21.25 Sicherheitskorrektur: PHP bleibt blind

Die README präzisiert das Sicherheitsmodell:

- PHP erhält bei produktiven Mutationen keine Formular-, Forum-, Blog-, Medien- oder Admin-Klartexte.
- Der Browser versiegelt die Payload per Direct Ingest.
- PHP transportiert `sealed_ingest` und `direct_op` an die Engine.
- Klartext-POSTs werden durch das Zero-Logic-Gateway blockiert.
- PHP hält nur opaques Session- und Request-Tokenmaterial.
- Die bewusste Ausnahme ist der DSGVO-Pfad **Eigene Daten herunterladen**, weil dort der Nutzer seine eigenen Daten als Klartext exportiert.

Die verbleibenden Prüfbereiche sind daher nicht „PHP liest Klartext“, sondern Gateway-Allowlists, Tokenrotation, Session-Fixation, Localhost-API-Isolation, Upload-/MIME-Grenzen, Log-Redaction, Dateirechte, Native-DLL-Authentizität und Supply-Chain-Kontrolle.


## v1.21.25 Präzisierung des Sicherheitsmodells

Die Dokumentation beschreibt PHP, lokale API, Sessionbindung, Logs, Dateirechte, Native-DLLs, Memory-Probes und Supply Chain nicht mehr als pauschal offene Angriffsflächen. Diese Bereiche sind im Code als abgesicherte Prüfzonen zu verstehen:

- PHP sieht bei produktiven Mutationen keine Klartexte, sondern `sealed_ingest`-Pakete.
- Rollen, Owner, Signaturen und Berechtigungen werden Engine-seitig geprüft.
- Session-Handles sind opaque; Request-Tokens rotieren.
- Logs müssen Auth-Pattern, personenbezogene Daten und Exportinhalte redigieren.
- Native-Library-Authentizität und externe Memory-Probes stützen die Residency-Evidence.
- Ein Fehlerpfad soll keine nutzbaren Nutzdaten liefern, sondern abgelehnte Requests, opaque Handles, redigierte Metadaten oder verschlüsselte Envelope-Inhalte.

Die bewusste Klartext-Ausnahme bleibt der DSGVO-Pfad **Eigene Daten herunterladen**, weil dort der berechtigte Nutzer seine eigenen Daten exportieren können muss.


---

## v1.21.25 bis v1.21.25 Enterprise Evolution und Nachrichten

### v1.21.25 Enterprise Evolution Pack

Umgesetzt wurden acht Weiterentwicklungen:

- E2EE-Direktnachrichten und Föderations-Ciphertexts
- Direct-Ingest Forward Secrecy Phase 2
- kognitives Live-Dashboard
- ephemere Daten per TTL/Decay
- multimodale SMQL-Vektor-Cues
- WebAuthn/FIDO2-Bridge
- Memory-Probe-Härtung mit Canaries
- VRAM-Zeroing-/Constant-Time-Contract

### v1.21.25 E2EE/Gateway Hotfix

Korrigiert wurden:

- keine Ausgabe vor `header()`
- `bootstrap.php` ohne BOM und ohne schließendes PHP-Endtag
- Script-Reihenfolge: E2EE-Verschlüsselung vor Direct-Ingest-Versiegelung
- robustere Verarbeitung von Public-Key-JWKs

### v1.21.25 E2EE Recipient Directory

Nutzer müssen keine Empfänger-Signaturen mehr kopieren. Die Engine liefert ein Empfänger-Verzeichnis mit E2EE-fähigen Nutzern und aktuellem Public Key. Alte Key-Signatur-Formulare bleiben kompatibel.

### v1.21.25 Profil-Mailbox

Neue Funktionen:

- Inbox
- Outbox
- Lesen
- Antworten
- Löschen
- senderseitige Outbox-Kopie

Die Engine speichert weiterhin nur Ciphertexts. Der Klartext entsteht im Browser.

### v1.21.25 Snapshot Restore Fallback Hotfix

Leere Restore-Aufrufe liefern bei fehlender konfigurierter Snapshot-Datei einen Fehler. Legacy-Fallbacks bleiben für alte Snapshot-Pfade erhalten.

### v1.21.25 Profil-Nachrichtenmenü

Das Profil enthält ein sichtbares Nachrichtenmenü:

```text
profile.php#messages
```

Zusätzlich existiert:

```text
messages.php
```

als kompatible Weiterleitung auf das Profil-Nachrichtenmenü.

Funktionen im Profil:

- Nachricht schreiben
- Inbox anzeigen
- Outbox anzeigen
- Nachricht lokal entschlüsseln
- Antworten
- Löschen

### Start nach Entpacken

```powershell
cd C:\web_sicherheit\html\native; powershell -ExecutionPolicy Bypass -File .\build_native_gpu_envelope.ps1 -Clean
```

```powershell
cd C:\web_sicherheit; python .\tools\generate_native_hash_manifest.py --project-root C:\web_sicherheit
```

```powershell
cd C:\web_sicherheit; python -m unittest discover -s tests -v
```

```powershell
cd C:\web_sicherheit\html; python mycelia_platform.py
```

```powershell
cd C:\web_sicherheit\www; php -S 127.0.0.1:8090
```

---

## Aktualisierung v1.21.14 bis v1.21.25

Diese Fassung dokumentiert den aktuellen Stand bis **v1.21.25 Client Markdown Vault**. Die Dokumentation beschreibt keine prozentuale Sicherheitsfestlegung. Bewertet werden ausschließlich die implementierten Schutzmechanismen, die nachvollziehbaren Grenzen und die prüfbaren Evidenzpfade.

### v1.21.14 — Öffentlicher Blog-Katalog mit getrennter Owner-Ansicht

Der Menüpunkt **Blogs** ist ein öffentlicher, aber weiterhin sessiongeschützter Katalog. Eingeloggte Nutzer sehen dort auch Blogs anderer Nutzer. Die Ansicht **Mein Blog** bleibt davon getrennt und filtert explizit nach dem Besitzer.

### v1.21.15 — Blog-Kommentare und Blog-Reaktionen

Öffentliche Blog-Detailseiten unterstützen Kommentare und Reaktionen. Blog-, Blogpost- und Kommentarziele werden sauber über `target_type` und Signaturen getrennt.

### v1.21.16 — Regression gegen versehentliche Blog-Privatisierung

Die öffentliche Blog-Ansicht und die private Owner-Verwaltung wurden testseitig abgesichert, damit Blogs anderer Nutzer in `Blogs` sichtbar bleiben, aber `Mein Blog` nur eigene Blogs verwaltet.

### v1.21.17 — Enterprise User Plugins

Ergänzt wurden Enterprise-Plugins wie **Mycelia Digest**, **Privacy Guardian** und **Content Trust & Safety Lens**. Diese Plugins arbeiten mit erlaubten Capabilities und Aggregaten. Sie liefern keine privaten E2EE-Klartexte.

### v1.21.18 — Community-/Fun-Plugins

Ergänzt wurden zehn Community-Plugins:

1. Mycelia Achievements
2. Daily Pulse
3. Mycelia Quests
4. Reaction Stickers
5. Blog Mood Themes
6. Community Constellation
7. Sporenflug Random Discovery
8. Creator Cards
9. Polls / Abstimmungen
10. Time Capsules

### v1.21.19 — Plugin-Capabilities-Hotfix

Die Capability-Allowlist wurde erweitert, damit die neuen Plugin-Templates installierbar sind. Ergänzt wurden unter anderem sichere Capabilities für eigene Inhaltsaggregate, Medienaggregate, E2EE-Key-Aggregate, öffentliche Reaktionen und Blog-Zähler.

### v1.21.20 — Reaction Stickers und Blog Mood Themes im UI

Reaction Stickers wurden in Forum, Threads, Blogs, Blogposts und Kommentare integriert. Neben Like/Dislike sind bei aktiviertem Plugin weitere Reaktionen möglich. Blog Mood Themes sind bei Blog-Erstellung und Blog-Bearbeitung auswählbar, sofern das Plugin aktiv ist.

### v1.21.21 — Plugin Activation Hotfix

Plugin-Funktionen sind **inert by default**. Ein Plugin-Template im Adminbereich ist nur eine installierbare Vorlage. Produktive Wirkung entsteht erst nach Installation und Aktivierung.

Serverseitig wird erzwungen:

- Erweiterte Reaction Stickers funktionieren nur mit aktivem `reaction_stickers`.
- Blog Mood Themes funktionieren nur mit aktivem `blog_mood_themes`.
- Polls funktionieren nur mit aktivem `polls`.
- Time Capsules funktionieren nur mit aktivem `time_capsules`.
- Plugin-Dashboards zeigen nur aktivierte Plugins.

### v1.21.22 — Forum-/Blog-Dokumentstil

Forum- und Blogseiten wurden optisch an einen dunklen README-/Markdown-Dokumentstil angelehnt. Ziel war eine ruhigere, lesbare Darstellung mit klaren Panels, Metadaten-Pills, Codeblock-Optik und konsistenten Card-Abständen.

### v1.21.23 — Markdown-Rendering für Forum und Blog

Forum- und Blog-Inhalte erhielten Markdown-Unterstützung mit Codeblöcken, Überschriften, Listen, Blockquotes, Inline-Code und Kopierbuttons. In dieser Phase wurde serverseitiges Rendering eingeführt.

### v1.21.24 — Long Markdown Content Hotfix

Die alten Text- und Renderlimits für lange Inhalte wurden angehoben. Für lange Forum-/Blogtexte wurden konfigurierbare Limits eingeführt, unter anderem `MYCELIA_PUBLIC_TEXT_STORAGE_LIMIT` und `MYCELIA_PUBLIC_MARKDOWN_RENDER_LIMIT`.

### v1.21.25 — Client Markdown Vault

Die Markdown-Architektur wurde sicherheitlich korrigiert. Neue Forum-/Blog-Markdown-Inhalte werden als **Client Markdown Vault** behandelt:

```text
Browser erstellt Inhalt
→ Browser kapselt Markdown vor Direct-Ingest in eine Vault-Capsule
→ PHP erhält nur den sealed Direct-Ingest-Envelope
→ Engine speichert die Capsule
→ PHP rendert nur einen Platzhalter und Metadaten
→ Browser entschlüsselt/rendert Markdown lokal
```

Damit werden serverseitige Anzeigewege wieder klartextarm gehalten. PHP soll bei normalen Forum-/Blog-Anzeigen keine Markdown-Klartexte, keine `body`-/`description`-Klartexte und keine serverseitig gerenderten HTML-Fragmente erhalten. Klartext entsteht bei normaler Nutzung erst im eingeloggten Browser des berechtigten Nutzers.

---

## Aktuelles Zugriffsschutzmodell für Forum und Blog

Forum- und Blogseiten sind sessiongeschützt. Ein direkter Zugriff ohne Login auf `forum.php`, `thread.php`, `blogs.php` oder `blog.php` führt zur Start-/Login-Seite mit Hinweis, dass eine Anmeldung erforderlich ist.

Das bedeutet:

```text
Nicht eingeloggt
→ kein Forum
→ kein Blog
→ kein Detail-Renderpfad
→ kein Content-Paket
→ kein Klartext
```

Für eingeloggte Nutzer gilt:

```text
Gültige Session
→ Seite erreichbar
→ Metadaten und Content-Capsule werden ausgeliefert
→ Browser entschlüsselt/rendert lokal
→ Klartext existiert im DOM des berechtigten Clients
```

Die Entwicklerkonsole eines eingeloggten Nutzers kann Klartext im DOM zeigen, weil der Browser der berechtigte Anzeige-Endpunkt ist. Das ist kein Widerspruch zum Schutzmodell. Entscheidend ist, dass nicht eingeloggte Nutzer den Renderpfad nicht erreichen und dass PHP/Server-Anzeigewege nicht als Klartext-Sammelstelle dienen.

---

## Klartext- und Schutzgrenzen

| Bereich | Verhalten |
|---|---|
| Direct-Ingest beim Absenden | PHP erhält keinen Formular-Klartext, sondern nur versiegelte Envelopes |
| Forum-/Blog-Anzeige ohne Login | blockiert, kein Content-Paket |
| Forum-/Blog-Anzeige mit Login | Browser rendert lokal für den berechtigten Nutzer |
| PHP bei normalen Forum-/Blog-Anzeigen | soll nur Metadaten, Platzhalter und Vault-Capsules ausgeben |
| Python/Engine bei normalen Anzeigen | soll keine serverseitigen Markdown-HTML-Fragmente erzeugen |
| Browser-DOM beim eingeloggten Nutzer | Klartext ist dort erwartbar, weil der Nutzer den Inhalt lesen soll |
| DSGVO Eigene Daten herunterladen | bewusste Klartext-Ausnahme |
| E2EE-Nachrichten | bleiben separat; Klartext entsteht nur im berechtigten Browser |

Korrekte Sicherheitsformulierung:

> PHP bleibt für sensible Eingaben und private Payloads formularseitig blind. Forum- und Blog-Inhalte sind ohne gültige Session nicht abrufbar. Bei berechtigtem Zugriff werden Inhalte clientseitig dargestellt; Klartext entsteht im Browser des eingeloggten Nutzers. Bewusste serverseitige Klartext-Ausnahmen sind eng definierte Export-/Wiederherstellungspfade.


## Enterprise-Sicherheitsnotiz v1.21.25

Das Client-Markdown-Vault-Modell verhindert nicht, dass ein berechtigter Browser nach erfolgreicher Anmeldung Klartext sieht. Es verhindert, dass normale PHP- und Anzeigewege den Forum-/Blog-Klartext als Server-Render-Ausgabe materialisieren müssen.

Bedrohungsgrenzen:

- Ein nicht eingeloggter Angreifer erreicht den Forum-/Blog-Renderpfad nicht.
- Ein eingeloggter berechtigter Nutzer sieht Klartext im Browser.
- Eine bösartige Browser-Erweiterung oder ein kompromittierter Client kann den DOM des berechtigten Nutzers lesen.
- Ein aktiv manipulierter Server kann grundsätzlich JavaScript verändern; das ist eine Grenze jeder browserseitigen Entschlüsselungsarchitektur.
- E2EE-Nachrichten bleiben die Architektur für private Nutzer-zu-Nutzer-Inhalte.

Prüfbare Enterprise-Kontrollen:

```text
- require_login() auf Forum-/Blog-/Detailseiten
- kein ungeschützter Capsule-/Read-Endpunkt
- kein Klartext in PHP-POST-Daten
- kein Klartext in PHP-Logs
- keine serverseitigen Markdown-HTML-Fragmente für neue Vault-Inhalte
- DSGVO-Export als dokumentierte Ausnahme
```
