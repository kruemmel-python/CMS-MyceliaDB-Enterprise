# MyceliaDB Enterprise Weboberfläche — Vollständiges Benutzer- und Admin-Handbuch v1.21.25

> **Version:** v1.21.25 Client Markdown Vault  
> **Zielgruppe:** neue Nutzer, Moderatoren, Administratoren und technische Betreiber  
> **Schwerpunkt:** sichere Bedienung der Weboberfläche ohne Vorwissen  
> **Sicherheitsformulierung:** Dieses Handbuch beschreibt konkrete implementierte Schutzmechanismen und Bedienpfade. Es verwendet keine prozentuale Sicherheitsfestlegung.

---

## Inhaltsverzeichnis

1. [Was ist MyceliaDB?](#1-was-ist-myceliadb)
2. [Wichtige Sicherheitsgrundsätze in einfachen Worten](#2-wichtige-sicherheitsgrundsätze-in-einfachen-worten)
3. [Erster Start der Weboberfläche](#3-erster-start-der-weboberfläche)
4. [Registrierung](#4-registrierung)
5. [Login](#5-login)
6. [Profilbereich](#6-profilbereich)
7. [Nachrichten Inbox/Outbox](#7-nachrichten-inboxoutbox)
8. [Forum benutzen](#8-forum-benutzen)
9. [Blogs benutzen](#9-blogs-benutzen)
10. [Medien: Bilder, GIFs und Videos](#10-medien-bilder-gifs-und-videos)
11. [Markdown schreiben wie auf GitHub](#11-markdown-schreiben-wie-auf-github)
12. [Reaction Stickers](#12-reaction-stickers)
13. [Spaß-Plugins](#13-spaß-plugins)
14. [E2EE und WebAuthn](#14-e2ee-und-webauthn)
15. [Datenschutz und eigene Daten](#15-datenschutz-und-eigene-daten)
16. [Admin-Bereich](#16-admin-bereich)
17. [Admin: Plugins installieren und aktivieren](#17-admin-plugins-installieren-und-aktivieren)
18. [Admin: Nutzer, Inhalte und Moderation](#18-admin-nutzer-inhalte-und-moderation)
19. [Admin: Sicherheit, Audits und Reports](#19-admin-sicherheit-audits-und-reports)
20. [Häufige Fragen](#20-häufige-fragen)
21. [Fehlerbehebung](#21-fehlerbehebung)
22. [Kurzübersicht: Rollen und Menüs](#22-kurzübersicht-rollen-und-menüs)

---

## 1. Was ist MyceliaDB?

MyceliaDB ist eine Webplattform mit Forum, Blogs, Profilen, Medienanhängen, Nachrichten, Datenschutzfunktionen, Plugin-System und Admin-Konsole.

Im Unterschied zu klassischen Webanwendungen arbeitet die Plattform mit einem bewusst reduzierten PHP-Frontend. PHP soll möglichst wenig Fachlogik und keinen sensiblen Formular-Klartext erhalten. Die eigentliche Verarbeitung läuft über die MyceliaDB-Engine.

Für normale Nutzer bedeutet das:

- Sie registrieren sich über die Weboberfläche.
- Sie melden sich an.
- Sie können Forum und Blogs nutzen.
- Sie können Bilder oder sichere Medienlinks anhängen.
- Sie können Markdown schreiben.
- Sie können, falls aktiviert, Reaction Stickers, Blog-Themes, Polls oder Time Capsules verwenden.
- Sie können ihre eigenen Daten exportieren oder löschen.

Für Administratoren bedeutet das:

- Nutzerrechte verwalten.
- Inhalte moderieren.
- Plugins installieren und aktivieren.
- Sicherheitsstatus und Auditberichte prüfen.
- Systemfunktionen kontrollieren.

---

## 2. Wichtige Sicherheitsgrundsätze in einfachen Worten

### 2.1 PHP soll nicht der Ort für Klartext sein

Die Weboberfläche nutzt PHP als Gateway und Anzeigehülle. Sensible Formulare werden im Browser versiegelt, bevor PHP sie erhält. PHP verarbeitet dadurch beim Absenden nicht den eigentlichen Formular-Klartext.

Typischer Ablauf beim Absenden:

```text
Browser
→ versiegelt Formularinhalt
→ PHP erhält nur verschlüsseltes Paket
→ Engine verarbeitet den Request
→ Antwort an Browser
```

### 2.2 Forum- und Blogtexte sind nur für eingeloggte Nutzer erreichbar

Wenn ein nicht eingeloggter Besucher direkt `forum.php`, `thread.php`, `blogs.php` oder `blog.php` öffnet, wird er zur Start-/Login-Seite geleitet.

Das bedeutet:

```text
Nicht eingeloggt
→ kein Forum
→ kein Blog-Renderpfad
→ kein Content-Paket
→ kein Klartext
```

### 2.3 Klartext im Browser ist normal

Ein eingeloggter und berechtigter Nutzer muss den Text lesen können. Deshalb entsteht Klartext am Ende im Browser des Nutzers. Das ist kein Fehler, sondern der gewünschte Anzeige-Endpunkt.

Wichtig ist die Trennung:

| Ort | Klartext erwünscht? | Erklärung |
|---|---:|---|
| PHP beim Absenden | Nein | Direct-Ingest hält PHP blind |
| PHP beim normalen Anzeigen | Nein, Zielmodell | PHP soll Platzhalter/Pakete ausgeben |
| Serverlogs | Nein | Logs sollen keine sensiblen Inhalte enthalten |
| Browser des eingeloggten Nutzers | Ja | Dort muss der Inhalt gelesen werden |
| DSGVO-Datenexport | Ja | Bewusste Ausnahme für eigene Daten |

### 2.4 Client Markdown Vault ab v1.21.25

Forum- und Blog-Markdown wird im Client-Modell behandelt. Die Weboberfläche zeigt Markdown wie bei GitHub an, inklusive Codeblöcken und Kopieren-Buttons. Die Architektur ist darauf ausgelegt, normale Anzeigewege nicht unnötig mit Markdown-Klartext in PHP zu belasten.

### 2.5 Plugins sind nicht automatisch aktiv

Ab v1.21.21 gilt:

```text
Plugin-Vorlage sichtbar
→ Admin installiert Plugin
→ Admin aktiviert Plugin
→ Funktion erscheint im UI
```

Beispiele:

- Reaction Stickers erscheinen erst nach Aktivierung des Plugins.
- Blog Mood Themes erscheinen erst nach Aktivierung des Plugins.
- Polls sind erst nach Aktivierung nutzbar.
- Time Capsules sind erst nach Aktivierung nutzbar.

---

## 3. Erster Start der Weboberfläche

Dieser Abschnitt ist für Betreiber oder lokale Tests gedacht. Normale Nutzer benötigen diese Schritte nicht.

### 3.1 Engine starten

In einem Terminal:

```powershell
cd D:\web_sicherheit\html
python mycelia_platform.py
```

Erwartung:

```text
MyceliaDB Platform listening on 127.0.0.1:9999
```

Falls GPU und Native Bridge aktiv sind, erscheinen zusätzlich Hinweise zur OpenCL-/VRAM-Initialisierung.

### 3.2 PHP-Webserver starten

In einem zweiten Terminal:

```powershell
cd D:\web_sicherheit\www
php -S 127.0.0.1:8090
```

Browser öffnen:

```text
http://127.0.0.1:8090
```

### 3.3 Zugriff aus dem LAN

Für Zugriff vom Smartphone oder einem anderen Gerät im LAN muss der PHP-Server auf einer erreichbaren Adresse laufen, zum Beispiel:

```powershell
cd D:\web_sicherheit\www
php -S 0.0.0.0:8081
```

Dann im Smartphone-Browser:

```text
http://IP-DES-PC:8081
```

Wichtig:

- Die IP ist die IP des Webserver-PCs, nicht die IP des Smartphones.
- Windows-Firewall muss den Port erlauben.
- Für Browser-Krypto-Funktionen kann ein sicherer Origin erforderlich sein. Für lokale Tests kann im Browser eine Ausnahme für den Origin gesetzt werden.

---

## 4. Registrierung

### 4.1 Registrierungsseite öffnen

Öffnen Sie die Startseite:

```text
http://127.0.0.1:8090
```

Auf der Startseite befindet sich ein Registrierungsbereich.

### 4.2 Benutzername und Passwort wählen

Geben Sie ein:

- Benutzername
- Passwort
- optional weitere Profildaten, falls angeboten

Empfehlungen:

- Verwenden Sie ein langes Passwort.
- Verwenden Sie kein Passwort, das bereits in anderen Diensten benutzt wird.
- Bewahren Sie Zugangsdaten sicher auf.

### 4.3 Registrierung absenden

Beim Absenden wird der Formularinhalt im Browser versiegelt. PHP erhält nicht den direkten Klartext des Formulars.

Nach erfolgreicher Registrierung können Sie sich einloggen.

### 4.4 Was passiert technisch?

Vereinfacht:

```text
Browser erstellt Direct-Ingest-Paket
PHP leitet Paket weiter
Engine prüft und speichert Nutzerattraktor
Autosnapshot persistiert Zustand
```

---

## 5. Login

### 5.1 Login ausführen

Auf der Startseite:

1. Benutzername eingeben.
2. Passwort eingeben.
3. Login absenden.

Nach erfolgreichem Login gelangen Sie zum Profil oder zur vorgesehenen Zielseite.

### 5.2 Login-Session

Nach dem Login erhält Ihre Browser-Sitzung einen gültigen Session-Kontext. Dieser wird verwendet, um Forum, Blogs, Profil, Plugins und weitere Bereiche freizuschalten.

### 5.3 Wenn der Login fehlschlägt

Prüfen Sie:

- Ist die Engine gestartet?
- Läuft der PHP-Webserver?
- Ist der Benutzername korrekt?
- Ist das Passwort korrekt?
- Wurde eventuell ein alter Snapshot entfernt oder ersetzt?

---

## 6. Profilbereich

Der Profilbereich ist die persönliche Startzentrale nach dem Login.

Typische Inhalte:

- Begrüßung
- eigene Signatur
- Stabilität/Storage-Hinweise
- Profilfelder
- Aktionen
- Nachrichten
- Plugin-Dashboards
- Datenschutzfunktionen

### 6.1 Eigene Signatur

Die Signatur ist ein öffentlicher technischer Identifikator innerhalb der Plattform. Sie dient zum Zuordnen von Inhalten, Reaktionen, Nachrichten und Besitzrechten.

Beispiel:

```text
d297d73acaedb56b248ad53f09c5c6b0e836b9b8aaefc48fefc51d05e27f5ae9
```

Die Signatur ist kein Passwort.

### 6.2 Profil bearbeiten

Im Profil können, je nach Formular, persönliche Angaben geändert werden:

- Vorname
- Nachname
- Straße
- Nummer
- PLZ
- Ort
- E-Mail

Nach dem Speichern werden die Daten über den geschützten Eingabepfad verarbeitet.

### 6.3 Aktionen im Profil

Typische Aktionsbuttons:

- Nachrichten Inbox/Outbox
- Enterprise Plugins
- Spaß-Plugins
- Forum öffnen
- Eigenen Blog verwalten
- Datenschutz & Datenexport
- Admin-Konsole, falls Admin

---

## 7. Nachrichten Inbox/Outbox

Die Nachrichtenfunktion dient zur direkten Kommunikation zwischen Nutzern.

### 7.1 Inbox

Die Inbox zeigt empfangene Nachrichten.

Typische Funktionen:

- Nachricht öffnen
- Nachricht lesen
- antworten
- löschen

### 7.2 Outbox

Die Outbox zeigt gesendete Nachrichten.

Typische Funktionen:

- gesendete Nachricht prüfen
- Verlauf nachvollziehen
- löschen, sofern vorgesehen

### 7.3 Empfänger finden

Falls ein Empfänger nicht über eine Signatur bekannt ist, sollte die Weboberfläche einen Empfänger über Benutzernamen oder Profilauswahl anbieten. Intern wird daraus die passende Signatur beziehungsweise der passende Public Key verwendet.

### 7.4 E2EE-Hinweis

E2EE-Nachrichten sind anders zu behandeln als öffentliche Forum-/Blog-Inhalte:

- Nachrichteninhalt soll nur für Absender und Empfänger lesbar sein.
- Die Engine speichert den verschlüsselten Blob.
- Nur der berechtigte Browser kann den Inhalt entschlüsseln.

---

## 8. Forum benutzen

### 8.1 Forum öffnen

Nach dem Login im Menü auf **Forum** klicken.

Nicht eingeloggte Nutzer werden zur Start-/Login-Seite geleitet.

### 8.2 Neuen Beitrag erstellen

Im Forum befindet sich ein Formular **Neuer Beitrag**.

Felder:

- Titel
- Beitrag
- optional Bild
- optional Medienlink
- optional Medientitel

Vorgehen:

1. Titel eingeben.
2. Beitrag schreiben.
3. Optional Bild oder Medienlink anhängen.
4. Absenden.

### 8.3 Beitrag ansehen

Ein Beitrag wird als Karte angezeigt. Enthalten sein können:

- Titel
- Autor
- Datum
- Stabilität
- Reaktionen
- Medien
- Markdown-Inhalt
- Kommentare

### 8.4 Beitrag kommentieren

Auf der Thread-Detailseite gibt es ein Kommentarfeld.

Vorgehen:

1. Kommentar eingeben.
2. Optional Medium anhängen.
3. Kommentar speichern.

### 8.5 Beitrag bearbeiten

Eigene Beiträge können, sofern erlaubt, bearbeitet werden. Admins können zusätzliche Moderationsrechte haben.

### 8.6 Beitrag löschen

Eigene Beiträge können, sofern erlaubt, gelöscht werden. Admins können Inhalte moderativ löschen.

### 8.7 Sicherheit im Forum

- Ohne Login kein Zugriff.
- Formulare werden über Direct-Ingest geschützt.
- Markdown wird für berechtigte Nutzer im Browser dargestellt.
- Ein nicht eingeloggter Angreifer kann keinen normalen Forum-Renderpfad auslösen.

---

## 9. Blogs benutzen

Es gibt zwei wichtige Blogbereiche:

| Menüpunkt | Bedeutung |
|---|---|
| Blogs | öffentlicher Blog-Katalog für eingeloggte Nutzer |
| Mein Blog | eigene Blogs erstellen und verwalten |

### 9.1 Öffentliche Blogs anzeigen

Klicken Sie auf **Blogs**.

Sie sehen Blogs anderer Nutzer, sofern diese im Katalog vorhanden sind.

### 9.2 Eigenen Blog erstellen

Klicken Sie auf **Mein Blog**.

Dort befindet sich ein Formular zum Erstellen eines Blogs.

Felder:

- Titel
- Beschreibung
- optional Blog Mood Theme, falls Plugin aktiv
- optional Bild oder Medienlink

### 9.3 Blog Mood Themes

Wenn das Plugin **Blog Mood Themes** installiert und aktiviert ist, kann ein Theme gewählt werden:

- Security
- Forschung
- Gaming
- Natur
- Kreativ
- Sci-Fi

Wenn das Plugin nicht aktiv ist, erscheint diese Auswahl nicht.

### 9.4 Blogpost erstellen

Innerhalb eines Blogs können Beiträge erstellt werden.

Typische Felder:

- Titel
- Inhalt
- optional Medium

### 9.5 Blog kommentieren

Eingeloggte Nutzer können öffentliche Blogs kommentieren, sofern die Funktion aktiv ist.

### 9.6 Blog liken oder reagieren

Core-Reaktionen Like/Dislike sind verfügbar. Erweiterte Reaction Stickers erscheinen erst, wenn das Plugin aktiviert wurde.

### 9.7 Blog bearbeiten oder löschen

Eigene Blogs können über **Mein Blog** verwaltet werden. Admins können moderativ eingreifen.

---

## 10. Medien: Bilder, GIFs und Videos

In Forum, Blogs und Kommentaren können Medien angehängt werden.

### 10.1 Bild hochladen

Erlaubte Formate:

- JPEG
- PNG
- GIF
- WebP

Typisches Limit:

```text
max 3 MB
```

### 10.2 Sicheren Medienlink verwenden

Statt Upload kann ein sicherer Link verwendet werden, zum Beispiel:

- YouTube
- Vimeo
- HTTPS-Bild

### 10.3 Medientitel

Ein Medientitel ist eine optionale Beschreibung für das Bild oder Video.

### 10.4 Sicherheit bei Medien

Medien werden nicht als beliebiger HTML-Code eingebettet. Es werden nur erlaubte, geprüfte Medienformen unterstützt.

---

## 11. Markdown schreiben wie auf GitHub

Forum und Blog unterstützen Markdown-ähnliche Formatierung.

### 11.1 Überschriften

```markdown
# Große Überschrift
## Abschnitt
### Unterabschnitt
```

### 11.2 Fett und kursiv

```markdown
**fett**
*kursiv*
```

### 11.3 Listen

```markdown
- Punkt 1
- Punkt 2
- Punkt 3
```

Nummerierte Liste:

```markdown
1. Erster Schritt
2. Zweiter Schritt
3. Dritter Schritt
```

### 11.4 Zitate

```markdown
> Dies ist ein Hinweis oder Zitat.
```

### 11.5 Inline-Code

```markdown
Der Befehl `python mycelia_platform.py` startet die Engine.
```

### 11.6 Codeblöcke

Für Codeblöcke drei Backticks verwenden:

````markdown
```powershell
cd D:\web_sicherheit\html
python mycelia_platform.py
```
````

In der Anzeige erscheint daraus ein Codeblock mit Kopieren-Button.

### 11.7 Links

```markdown
[Linktext](https://example.com)
```

Hinweis: Die Plattform sollte Links sicher behandeln. Unbekannte oder unsichere Links sollten nicht blind geöffnet werden.

### 11.8 Sehr lange Texte

Ab v1.21.24 sind lange Markdown-Inhalte vorgesehen. Trotzdem empfiehlt sich für Lesbarkeit:

- Abschnitte mit Überschriften trennen.
- Große Codeblöcke sinnvoll beschriften.
- Sehr lange Texte in mehrere Posts aufteilen, wenn Diskussionen getrennt bleiben sollen.

---

## 12. Reaction Stickers

### 12.1 Core-Reaktionen

Standardmäßig verfügbar:

- Like
- Dislike

### 12.2 Erweiterte Reaction Stickers

Nach Aktivierung des Plugins **Reaction Stickers** erscheinen zusätzliche Reaktionen:

- Stark
- Lustig
- Herz
- Interessant
- Danke
- Nachdenklich

### 12.3 Wo Reaktionen nutzbar sind

Reaktionen können je nach Seite genutzt werden bei:

- Forum-Beiträgen
- Forum-Kommentaren
- Blogs
- Blogposts
- Blog-Kommentaren

### 12.4 Wenn Stickers nicht sichtbar sind

Prüfen:

1. Ist das Plugin installiert?
2. Ist das Plugin aktiviert?
3. Wurde die Seite neu geladen?
4. Ist der Nutzer eingeloggt?

---

## 13. Spaß-Plugins

Spaß-Plugins erweitern die Nutzererfahrung. Sie sind nicht automatisch aktiv.

### 13.1 Verfügbare Spaß-Plugins

| Plugin | Zweck |
|---|---|
| Mycelia Achievements | Badges und Erfolge |
| Daily Pulse | täglicher Community-Puls |
| Mycelia Quests | spielerische Aufgaben |
| Reaction Stickers | zusätzliche Reaktionen |
| Blog Mood Themes | Blog-Themes |
| Community Constellation | aggregierte Community-Übersicht |
| Sporenflug Random Discovery | zufällige Entdeckung |
| Creator Cards | öffentliche Creator-Karten |
| Polls | Abstimmungen |
| Time Capsules | Zeitkapseln |

### 13.2 Spaß-Plugins öffnen

Im Menü auf **Spaß-Plugins** klicken.

Wenn keine Plugins aktiv sind, erscheint ein Hinweis. Erst nach Installation und Aktivierung durch den Admin werden Funktionen sichtbar.

### 13.3 Polls

Wenn aktiv:

1. Frage eingeben.
2. Mindestens zwei Optionen eingeben.
3. Umfrage erstellen.
4. Nutzer stimmen ab.

### 13.4 Time Capsules

Wenn aktiv:

1. Titel eingeben.
2. Inhalt schreiben.
3. Reveal-Zeitpunkt festlegen.
4. Sichtbarkeit wählen.
5. Speichern.

---

## 14. E2EE und WebAuthn

### 14.1 E2EE

E2EE ist für private Kommunikation relevant. Dabei bleiben Inhalte so verschlüsselt, dass nur berechtigte Browser sie entschlüsseln können.

Typische Bereiche:

- Direktnachrichten
- private Payloads
- Empfängerbezogene Inhalte

### 14.2 Public Keys

Im E2EE-Bereich können Public Keys sichtbar sein. Diese dienen dazu, Nachrichten an einen Nutzer zu verschlüsseln.

### 14.3 WebAuthn

WebAuthn kann für stärkere Authentifizierung genutzt werden, zum Beispiel mit:

- Windows Hello
- Apple Face ID / Touch ID
- Security Keys
- Plattform-Authenticator

Falls WebAuthn noch nicht eingerichtet ist, bleibt der normale Loginpfad aktiv.

---

## 15. Datenschutz und eigene Daten

Der Datenschutzbereich ermöglicht dem Nutzer Kontrolle über eigene Daten.

### 15.1 Eigene Daten herunterladen

Dies ist eine bewusste Klartext-Ausnahme. Der Nutzer fordert seine eigenen Daten an und bekommt sie in lesbarer Form.

### 15.2 Eigene Daten löschen

Je nach Implementierung kann der Nutzer eigene Daten löschen oder eine Löschung auslösen. Löschfunktionen können zusätzliche Bestätigung verlangen.

### 15.3 Warum ist Export eine Ausnahme?

Ein Nutzer muss seine eigenen Daten lesen und sichern können. Daher ist der Export ein definierter Pfad, bei dem Klartext bewusst erzeugt wird.

---

# 16. Admin-Bereich

Dieser Bereich richtet sich an Administratoren.

Admins haben zusätzliche Rechte. Der Adminbereich sollte nur von vertrauenswürdigen Nutzern verwendet werden.

## 16.1 Admin-Konsole öffnen

Nach dem Login als Admin erscheint im Menü oder Profil ein Link:

```text
Admin
```

oder:

```text
Admin-Konsole
```

Wenn der Link nicht sichtbar ist:

- Sind Sie als Admin eingeloggt?
- Hat Ihr Nutzer die Admin-Rolle?
- Wurde die Session korrekt geladen?

## 16.2 Admin-Grundprinzip

Der Admin soll verwalten, aber nicht unnötig Klartext sehen. Die Plattform arbeitet mit Rollen, Tokens, Engine-Kommandos und geschützten Pfaden.

Adminaktionen sollten immer bewusst ausgeführt werden.

---

## 17. Admin: Plugins installieren und aktivieren

### 17.1 Plugin-Lifecycle

Ab v1.21.21 gilt:

```text
Plugin-Vorlage
→ installieren
→ aktivieren
→ Funktion ist sichtbar und nutzbar
```

Ein Plugin ist also nicht aktiv, nur weil es im Katalog sichtbar ist.

### 17.2 Plugin-Katalog öffnen

Im Admin-Menü:

1. **Plugins** öffnen.
2. Verfügbare Plugin-Vorlagen ansehen.
3. Gewünschtes Plugin auswählen.

### 17.3 Plugin installieren

Beim Installieren wird das Manifest des Plugins als kontrollierter Plugin-Attraktor gespeichert.

Der Admin sollte prüfen:

- Name
- Version
- Beschreibung
- Capabilities
- Hooks
- Constraints

### 17.4 Plugin aktivieren

Nach Installation muss das Plugin aktiviert werden.

Erst dann:

- erscheint die UI-Funktion
- werden abhängige Aktionen freigeschaltet
- akzeptiert der Server pluginabhängige Requests

### 17.5 Plugin deaktivieren

Ein deaktiviertes Plugin bleibt installiert, aber seine Funktion ist nicht produktiv nutzbar.

Beispiele:

| Plugin | Effekt der Deaktivierung |
|---|---|
| Reaction Stickers | nur Like/Dislike bleiben |
| Blog Mood Themes | Theme-Auswahl verschwindet |
| Polls | Umfragen nicht nutzbar |
| Time Capsules | Zeitkapseln nicht nutzbar |

### 17.6 Plugin löschen

Ein Plugin kann aus der Installation entfernt werden. Je nach Plugin bleiben bereits erzeugte Daten als gespeicherte Attraktoren erhalten oder werden nicht mehr angezeigt. Administratoren sollten vor Löschung prüfen, ob Nutzerdaten betroffen sind.

---

## 18. Admin: Nutzer, Inhalte und Moderation

### 18.1 Nutzer verwalten

Admins können, je nach Oberfläche, Nutzer prüfen und Rechte ändern.

Mögliche Aufgaben:

- Nutzerstatus prüfen
- Rollen ändern
- Rechte entziehen
- verdächtige Nutzer sperren
- Berechtigung zur Forumserstellung steuern

### 18.2 Forum moderieren

Admins können Forum-Inhalte moderieren:

- Beiträge prüfen
- Beiträge löschen
- Kommentare löschen
- Medien prüfen
- Reaktionsmissbrauch beobachten

### 18.3 Blogs moderieren

Admins können Blog-Inhalte moderieren:

- Blogs prüfen
- Blogposts löschen
- Kommentare löschen
- Medien prüfen
- unangemessene Inhalte entfernen

### 18.4 Medien moderieren

Medien sollten geprüft werden, wenn:

- ein Link verdächtig aussieht
- ein Bild nicht zum Beitrag passt
- ein externer Anbieter eingebettet wird
- Nutzer Missbrauch melden

### 18.5 Moderationsprinzip

Empfohlen:

1. Erst prüfen.
2. Dann moderieren.
3. Möglichst dokumentieren.
4. Keine unnötigen Daten exportieren.
5. Bei Sicherheitsverdacht Logs/Audit prüfen.

---

## 19. Admin: Sicherheit, Audits und Reports

### 19.1 Sicherheitsstatus prüfen

Der Adminbereich kann maschinenlesbare Sicherheitsstatusberichte anzeigen. Diese sind wichtig für:

- Native Bridge Status
- VRAM-/GPU-Residency-Hinweise
- Direct-Ingest-Status
- Session-/Tokenbindung
- Log-Redaction
- Snapshot-Status
- Heartbeat-Audit

### 19.2 Native Library Hash Manifest

Nach Änderungen an nativen Bibliotheken sollte das Hashmanifest aktualisiert werden:

```powershell
cd D:\web_sicherheit
python .\tools\generate_native_hash_manifest.py --project-root D:\web_sicherheit
```

### 19.3 Tests ausführen

Nach Updates:

```powershell
cd D:\web_sicherheit
python -m unittest discover -s tests -v
```

### 19.4 Compile-Check

```powershell
cd D:\web_sicherheit
python -m compileall html tools tests
```

### 19.5 PHP-Lint

Für wichtige Webdateien:

```powershell
php -l www\bootstrap.php
php -l www\forum.php
php -l www\thread.php
php -l www\blogs.php
php -l www\blog.php
php -l www\my_blog.php
```

### 19.6 Snapshot-Probleme

Wenn ein Autosnapshot nicht geladen werden kann, kann er beschädigt oder aus einer alten Version sein.

Sicheres Vorgehen:

```powershell
cd D:\web_sicherheit
New-Item -ItemType Directory -Force .\html\snapshots_broken | Out-Null
if (Test-Path .\html\snapshots\autosave.mycelia) {
  Move-Item .\html\snapshots\autosave.mycelia .\html\snapshots_broken\autosave_broken_$(Get-Date -Format yyyyMMdd_HHmmss).mycelia
}
```

Danach Engine neu starten.

Achtung: Dadurch startet das System ohne den alten Snapshot-Zustand, sofern kein anderer Snapshot wiederhergestellt wird.

### 19.7 Prüfen, ob Forum/Blog ohne Login blockiert sind

In einem nicht eingeloggten Browser:

```text
http://SERVER/forum.php
http://SERVER/thread.php?id=THREADSIGNATUR
http://SERVER/blogs.php
http://SERVER/blog.php?id=BLOGSIGNATUR
```

Erwartung:

```text
Login-Hinweis oder Startseite
```

### 19.8 Prüfen, ob Klartext nicht im Seitenquelltext steht

Für berechtigte Nutzer gilt:

- Im gerenderten DOM darf sichtbarer Text stehen.
- Im Seitenquelltext und in Serverantworten sollte kein unnötiger Klartext stehen, sofern Vault-/Capsule-Pfad genutzt wird.

Prüfen:

1. Rechtsklick → Seitenquelltext anzeigen.
2. Nach eindeutigem Testtext suchen.
3. DevTools → Network → Response prüfen.
4. Testtext sollte nicht als serverseitig ausgelieferter Klartext erscheinen.

---

## 20. Häufige Fragen

### 20.1 Warum sehe ich im Browser-Konsolen-DOM Klartext?

Weil Sie eingeloggt und berechtigt sind. Der Browser muss den Inhalt anzeigen. Der Klartext im eigenen Browser ist der gewünschte Endpunkt.

### 20.2 Ist Klartext in der Entwicklerkonsole ein Sicherheitsproblem?

Nicht automatisch. Entscheidend ist, ob der Klartext bereits im Server-HTML, in PHP, Logs oder API-Antworten erscheint. Im gerendeten Browser-DOM des berechtigten Nutzers ist Klartext normal.

### 20.3 Warum sehe ich ohne Login nur die Startseite?

Das ist korrekt. Ohne Session sollen Forum und Blog nicht erreichbar sein.

### 20.4 Warum sehe ich keine Reaction Stickers?

Das Plugin ist wahrscheinlich nicht installiert oder nicht aktiviert. Der Admin muss es aktivieren.

### 20.5 Warum sehe ich keine Blog-Themes?

Das Plugin **Blog Mood Themes** ist wahrscheinlich nicht aktiv.

### 20.6 Warum kann ich keine Polls erstellen?

Das Plugin **Polls** ist nicht aktiv oder Sie sind nicht eingeloggt.

### 20.7 Warum kann ich keine Time Capsule erstellen?

Das Plugin **Time Capsules** ist nicht aktiv oder Sie sind nicht eingeloggt.

### 20.8 Warum kommt ein Browser-Extension-Fehler in der Console?

Meldungen wie:

```text
Could not establish connection. Receiving end does not exist.
```

kommen häufig von Browser-Erweiterungen. Testen Sie in einem privaten Fenster ohne Extensions oder in einem anderen Browser.

### 20.9 Warum blockiert der Browser Tracking Storage?

Meldungen zu `safeframe.googlesyndication.com` oder Tracking Prevention kommen oft von externen Embeds oder Browser-Schutzfunktionen. Sie bedeuten nicht automatisch einen MyceliaDB-Fehler.

---

## 21. Fehlerbehebung

### 21.1 Seite lädt nicht

Prüfen:

```powershell
Get-NetTCPConnection -LocalPort 8090 -ErrorAction SilentlyContinue
```

Oder für LAN-Port:

```powershell
Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
```

### 21.2 Engine nicht erreichbar

Prüfen, ob Terminal 1 läuft:

```powershell
cd D:\web_sicherheit\html
python mycelia_platform.py
```

### 21.3 Smartphone erreicht Webserver nicht

Prüfen:

- PHP läuft mit `0.0.0.0:PORT`.
- Windows-Firewall erlaubt den Port.
- Smartphone ist im selben LAN.
- IP des PCs wird verwendet.
- Kein VPN blockiert LAN-Zugriff.

Firewall-Regel:

```powershell
New-NetFirewallRule -DisplayName "MyceliaDB PHP LAN 8081" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8081
```

### 21.4 WebCrypto am Smartphone funktioniert nicht

Browser-Krypto-APIs benötigen sichere Origins. Bei lokalen Tests kann eine Browser-Ausnahme notwendig sein.

Für Edge/Chrome-Testumgebungen:

```text
Insecure origins treated as secure
```

Dort muss die Origin des Webservers eingetragen werden, zum Beispiel:

```text
http://192.168.178.65:8081
```

Danach Browser neu starten.

### 21.5 Plugin lässt sich nicht installieren

Prüfen:

- Ist der Nutzer Admin?
- Ist das Manifest gültig?
- Fordert das Plugin nur erlaubte Capabilities?
- Ist der Plugin-Katalog aktuell?
- Wurde die richtige Projektversion entpackt?

### 21.6 Plugin installiert, aber Funktion nicht sichtbar

Prüfen:

- Wurde das Plugin auch aktiviert?
- Seite neu laden.
- Neu einloggen, falls Session alt ist.
- Adminbereich prüfen, ob `enabled` aktiv ist.

### 21.7 Bilder oder Videos werden nicht angezeigt

Prüfen:

- Ist der Dateityp erlaubt?
- Ist die Datei kleiner als das Limit?
- Ist der Medienlink erlaubt?
- Ist der Beitrag gespeichert?
- Gibt es Browser-Blocker für externe Medien?

### 21.8 Langer Markdown-Text wird nicht vollständig angezeigt

Ab v1.21.24 gibt es erhöhte Langtext-Limits. Falls weiterhin etwas fehlt:

- Wurde die aktuelle Version verwendet?
- Ist der Text wirklich gespeichert?
- Browsercache leeren.
- Engine und PHP neu starten.
- Snapshot prüfen.

---

## 22. Kurzübersicht: Rollen und Menüs

### 22.1 Normaler Nutzer

| Menü | Zweck |
|---|---|
| Profil | eigene Daten, Aktionen |
| Nachrichten | Inbox/Outbox |
| Spaß-Plugins | aktive Community-Plugins |
| Live-Dashboard | Status-/Visualisierung, falls verfügbar |
| E2EE | Schlüssel und verschlüsselte Kommunikation |
| WebAuthn | starke Authentifizierung |
| Forum | Beiträge und Kommentare |
| Blogs | öffentliche Blogs eingeloggter Nutzer |
| Mein Blog | eigene Blogs verwalten |
| Datenschutz | Export/Löschung eigener Daten |
| Logout | abmelden |

### 22.2 Admin

Zusätzlich:

| Menü | Zweck |
|---|---|
| Plugins | Plugin-Katalog, Installation, Aktivierung |
| Admin | Nutzer, Inhalte, Sicherheit, Moderation |

### 22.3 Betreiber

Zusätzlich außerhalb der Weboberfläche:

| Aufgabe | Befehl |
|---|---|
| Engine starten | `python mycelia_platform.py` |
| PHP starten | `php -S 127.0.0.1:8090` |
| Native Bridge bauen | `build_native_gpu_envelope.ps1 -Clean` |
| Hashmanifest erzeugen | `generate_native_hash_manifest.py` |
| Tests ausführen | `python -m unittest discover -s tests -v` |

---

## Abschluss

Dieses Handbuch beschreibt die Weboberfläche von MyceliaDB Enterprise v1.21.25 aus Nutzer- und Adminsicht.

Die wichtigste Bedienlogik lautet:

```text
Registrieren
→ Einloggen
→ Profil prüfen
→ Forum oder Blogs nutzen
→ Medien und Markdown verwenden
→ Plugins nur nutzen, wenn Admin sie aktiviert hat
→ Datenschutzbereich für eigene Daten verwenden
```

Die wichtigste Adminlogik lautet:

```text
System starten und prüfen
→ Nutzer und Inhalte moderieren
→ Plugins kontrolliert installieren
→ Plugins erst bewusst aktivieren
→ Sicherheitsstatus und Audits prüfen
→ keine unnötigen Klartextpfade öffnen
```
