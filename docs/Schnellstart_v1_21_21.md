# Schnellstart.md — MyceliaDB Enterprise v1.21.21

> Hinweis zu Sicherheitsformulierungen: Diese Dokumentation beschreibt die implementierten Schutzmechanismen und prüfbaren Evidenzpfade. Es wird keine prozentuale Sicherheitsfestlegung verwendet. Entscheidend sind die konkret umgesetzten Mechanismen: Zero-Logic-Gateway, Direct-Ingest, Native-VRAM-Pfade, Session-/Tokenbindung, Log-Redaction, Snapshot-Verschlüsselung, E2EE-Mailbox und prüfbare Auditberichte.


Diese Schnellstart-Anleitung zeigt die wichtigsten PowerShell-Einzeiler, um MyceliaDB Enterprise zu starten, die Webseite zu nutzen und die wichtigsten Sicherheits-/Auditfunktionen auszuführen.

> Annahme: Das Projekt liegt unter `D:\web_sicherheit`.

---

## 1. In das Projektverzeichnis wechseln

```powershell
cd D:\web_sicherheit
```

Wechselt in das Hauptverzeichnis des Projekts.

---

## 2. Native GPU Envelope DLL bauen

```powershell
cd D:\web_sicherheit\html\native; powershell -ExecutionPolicy Bypass -File .\build_native_gpu_envelope.ps1 -Clean
```

Baut die native VRAM-/GPU-Envelope-DLL `mycelia_gpu_envelope.dll`.

Erwartete Datei:

```text
D:\web_sicherheit\html\native\mycelia_gpu_envelope.dll
```

---

## 3. Prüfen, ob der OpenCL-Build-Ordner vorhanden ist

```powershell
Test-Path D:\web_sicherheit\build\CC_OpenCl.dll
```

Prüft, ob die Core-OpenCL-DLL vorhanden ist.

Erwartung:

```text
True
```

Falls `False`, muss der Ordner `build` aus dem Projekt-/Build-Paket wiederhergestellt werden.

---

## 4. Native-Library-Hash-Manifest erzeugen

```powershell
cd D:\web_sicherheit; python .\tools\generate_native_hash_manifest.py --project-root D:\web_sicherheit
```

Erzeugt oder aktualisiert das Manifest zur DLL-Authentizitätsprüfung.

Wichtig für:

- `CC_OpenCl.dll`
- `mycelia_gpu_envelope.dll`
- Schutz gegen DLL-Hijacking / Proxy-DLLs

---

## 5. MyceliaDB Engine im normalen Webmodus starten

```powershell
cd D:\web_sicherheit\html; python mycelia_platform.py
```

Startet die Python/OpenCL-Engine auf:

```text
http://127.0.0.1:9999/
```

Dieser Modus ist für normale Webnutzung geeignet.

---

## 6. MyceliaDB Engine im Strict-VRAM-Auditmodus starten

```powershell
cd D:\web_sicherheit\html; $env:MYCELIA_STRICT_VRAM_CERTIFICATION="1"; $env:MYCELIA_STRICT_RESPONSE_REDACTION="1"; $env:MYCELIA_AUTORESTORE="0"; python mycelia_platform.py
```

Startet die Engine für den Strict-VRAM-Evidence-Audit.

Wichtig:

- Danach zunächst **keine Weboberfläche öffnen**.
- Erst den Random-Secret-Memory-Probe ausführen.
- `MYCELIA_AUTORESTORE=0` verhindert Python-materialisierten Restore während des Audits.

---

## 7. PHP-Webseite starten

```powershell
cd D:\web_sicherheit\www; php -S 127.0.0.1:8090
```

Startet das Web-Frontend.

Danach im Browser öffnen:

```text
http://127.0.0.1:8090/
```

---

## 8. Webseite nutzen

```powershell
Start-Process "http://127.0.0.1:8090/"
```

Öffnet die MyceliaDB-Webseite im Standardbrowser.

Dort verfügbar:

- Registrierung
- Login
- Profil
- Forum
- Blog
- Mein Blog
- Admin-Panel
- Plugin-Panel
- Datenschutz-Center
- VRAM-/Heartbeat-Audit-Dashboard

---

## 9. Admin-Panel öffnen

```powershell
Start-Process "http://127.0.0.1:8090/admin.php"
```

Öffnet das Admin-Dashboard.

Dort verfügbar:

- Benutzerrechte
- Webseitentexte
- Forum-/Blog-Moderation
- VRAM-Evidence
- Heartbeat-Audit
- SMQL-Test
- Föderationsstatus
- Provenance-Verifikation
- Native-Library-Authentizität
- Localhost-Transport-Security
- Quantum-Guard-Status

---

## 10. Plugin-Panel öffnen

```powershell
Start-Process "http://127.0.0.1:8090/plugins.php"
```

Öffnet das Plugin-Admin-Panel.

Plugins sind keine PHP-/Python-Dateien, sondern deklarative Mycelia-Attraktor-Manifeste.

---

## 11. Datenschutz-Center öffnen

```powershell
Start-Process "http://127.0.0.1:8090/privacy.php"
```

Öffnet das Datenschutz-Center.

Dort verfügbar:

- eigene Daten als JSON herunterladen
- Account löschen
- DSGVO-orientierte Export-/Löschfunktionen

---

## 12. Engine-Integrität prüfen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"check_integrity","payload":{}}' | ConvertTo-Json -Depth 20
```

Prüft den Engine-Zustand, SQL-Freiheit, Native-Status, GPU-Status und Enterprise-v1.20-Erweiterungen.

---

## 13. Native GPU Capability Report abrufen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"native_gpu_capability_report","payload":{}}' | ConvertTo-Json -Depth 30
```

Zeigt den Status der Native-VRAM-Bridge.

Wichtige Felder:

- `available`
- `envelope_to_vram`
- `snapshot_to_vram`
- `native_command_executor`
- `native_snapshot_runtime`
- `native_persistence_mutation`
- `native_strict_certification_gate`

---

## 14. Native GPU Selftest ausführen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"native_gpu_residency_selftest","payload":{}}' | ConvertTo-Json -Depth 30
```

Führt den nativen VRAM-Selftest aus.

Erwartete zentrale Felder:

```json
"strict_vram_residency": true,
"plaintext_returned_to_python": false
```

---

## 15. Strict-VRAM Random-Secret-Audit ausführen

```powershell
cd D:\web_sicherheit; $secret = "VRAM_ONLY_" + [guid]::NewGuid().ToString("N"); [System.IO.File]::WriteAllLines("D:\web_sicherheit\strict_random_probe.txt", @($secret), [System.Text.UTF8Encoding]::new($false)); $manifest = Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"residency_audit_manifest","payload":{}}'; python D:\web_sicherheit\tools\mycelia_memory_probe.py --pid $manifest.pid --challenge-id $manifest.challenge_id --probe-file D:\web_sicherheit\strict_random_probe.txt --json-out D:\web_sicherheit\residency_probe_random.json; $report = Get-Content D:\web_sicherheit\residency_probe_random.json -Raw; $body = @{ command = "submit_external_memory_probe"; payload = ($report | ConvertFrom-Json) } | ConvertTo-Json -Depth 20; Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body $body; Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"strict_vram_evidence_bundle","payload":{}}' | ConvertTo-Json -Depth 30
```

Führt den vollständigen Strict-VRAM-Audit mit frischem Random-Secret aus.

Zielwerte:

```json
"strict_hits": 0,
"strict_negative": true,
"negative_cpu_ram_probe": true,
"last_restore_cpu_materialized": false,
```

---

## 16. Heartbeat-Audit einmalig ausführen

```powershell
cd D:\web_sicherheit; powershell -ExecutionPolicy Bypass -File .\tools\run_heartbeat_audit.ps1 -ProjectRoot D:\web_sicherheit -Engine http://127.0.0.1:9999/
```

Führt den geplanten Hardware-Residency-Heartbeat manuell aus.

Der Heartbeat:

- erzeugt ein frisches Random-Secret
- führt den externen Memory-Probe aus
- reicht Evidence bei der Engine ein
- erzeugt ein signiertes Ergebnis
- aktualisiert den Admin-Dashboard-Status

---

## 17. Heartbeat-Audit täglich als Windows Scheduled Task installieren

```powershell
cd D:\web_sicherheit; powershell -ExecutionPolicy Bypass -File .\tools\install_heartbeat_audit_task.ps1 -ProjectRoot D:\web_sicherheit -Engine http://127.0.0.1:9999/ -At 03:15
```

Installiert den täglichen Heartbeat-Audit um 03:15 Uhr.

Voraussetzung:

- Engine muss zum geplanten Zeitpunkt laufen.
- Strict-VRAM-Modus muss aktiv sein, wenn eine Strict-VRAM-Evidence-Bewertung erzeugt werden soll.

---

## 18. Heartbeat-Audit-Status abrufen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"heartbeat_audit_status","payload":{}}' | ConvertTo-Json -Depth 20
```

Zeigt den letzten signierten Heartbeat-Audit.

Wichtige Felder:

- `certified`
- `signed`
- `received_at`
- `expires_at`

---

## 19. SMQL-Abfrage erklären

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"smql_explain","payload":{"query":"FIND mycelia_users WHERE role=admin ASSOCIATED WITH \"High Security\" LIMIT 10"}}' | ConvertTo-Json -Depth 20
```

Parst eine SMQL-Abfrage und zeigt, wie sie in deterministische Filter und semantische Cues übersetzt wird.

---

## 20. SMQL-Abfrage ausführen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"smql_query","payload":{"query":"FIND mycelia_users WHERE role=admin ASSOCIATED WITH \"High Security\" LIMIT 10"}}' | ConvertTo-Json -Depth 20
```

Führt eine semantisch-strukturierte MyceliaDB-Abfrage aus.

---

## 21. Föderationsstatus anzeigen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"federation_status","payload":{}}' | ConvertTo-Json -Depth 20
```

Zeigt den Status der Myzel-Föderation.

---

## 22. Föderations-Peer hinzufügen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"federation_peer_add","payload":{"peer_id":"node-b","url":"https://127.0.0.1:9998/","trust":"manual"}}' | ConvertTo-Json -Depth 20
```

Fügt einen Remote-Mycelia-Knoten als Föderations-Peer hinzu.

Hinweis: Für produktive Nutzung sollte mTLS aktiviert und der Peer-Fingerprint geprüft werden.

---

## 23. Föderations-Sync-Tool ausführen

```powershell
cd D:\web_sicherheit; python .\tools\mycelia_federation_sync.py --engine http://127.0.0.1:9999/
```

Synchronisiert stabile Attraktoren zwischen konfigurierten Föderations-Peers.

---

## 24. Provenance-Log anzeigen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"provenance_log","payload":{"limit":20}}' | ConvertTo-Json -Depth 20
```

Zeigt die letzten Provenance-/Lineage-Ereignisse.

---

## 25. Provenance-Ledger verifizieren

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"provenance_verify","payload":{}}' | ConvertTo-Json -Depth 20
```

Verifiziert die Hash-Kette des kryptografischen Provenance-Ledgers.

---

## 26. Localhost Transport Security prüfen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"local_transport_security_status","payload":{}}' | ConvertTo-Json -Depth 20
```

Zeigt den Status des lokalen Transport-Schutzes.

Wichtig:

- Local Token Binding schützt gegen einfache Localhost-Proxy-/MITM-Fehler.
- Optional kann lokales HTTPS aktiviert werden.

---

## 27. Localhost-TLS-Zertifikat erzeugen

```powershell
cd D:\web_sicherheit; python .\tools\generate_localhost_tls.py --project-root D:\web_sicherheit
```

Erzeugt lokale TLS-Dateien für optionales HTTPS zwischen PHP und Engine.

Optionaler Start der Engine mit lokalem HTTPS:

```powershell
cd D:\web_sicherheit\html; $env:MYCELIA_LOCAL_HTTPS="1"; python mycelia_platform.py
```

---

## 28. Native-Library-Authentizität prüfen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"native_library_authenticity","payload":{}}' | ConvertTo-Json -Depth 20
```

Prüft, ob die geladenen Native-Libraries mit dem Hash-Manifest übereinstimmen.

Schützt gegen:

- DLL-Hijacking
- Proxy-DLLs
- falsche Bibliotheken im Suchpfad

---

## 29. Quantum Guard Status prüfen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"quantum_guard_status","payload":{}}' | ConvertTo-Json -Depth 20
```

Zeigt Token-Bucket, Cooldown und Circuit-Breaker-Zustand des Quantum-Oracle-/Tension-Guards.

---

## 30. Tests ausführen

```powershell
cd D:\web_sicherheit; python -m unittest discover -s tests -v
```

Führt die gesamte Python-Test-Suite aus.

---

## 31. PHP-Syntax prüfen

```powershell
cd D:\web_sicherheit; Get-ChildItem .\www -Filter *.php | ForEach-Object { php -l $_.FullName }
```

Prüft alle PHP-Dateien auf Syntaxfehler.

---

## 32. Typischer Betriebsstart für normale Webseite

```powershell
Start-Process powershell -ArgumentList '-NoExit','-Command','cd D:\web_sicherheit\html; python mycelia_platform.py'; Start-Sleep -Seconds 2; Start-Process powershell -ArgumentList '-NoExit','-Command','cd D:\web_sicherheit\www; php -S 127.0.0.1:8090'; Start-Sleep -Seconds 1; Start-Process "http://127.0.0.1:8090/"
```

Startet Engine und PHP-Webseite in zwei PowerShell-Fenstern und öffnet die Webseite.

---

## 33. Typischer Betriebsstart für Strict-VRAM-Audit

```powershell
Start-Process powershell -ArgumentList '-NoExit','-Command','cd D:\web_sicherheit\html; $env:MYCELIA_STRICT_VRAM_CERTIFICATION="1"; $env:MYCELIA_STRICT_RESPONSE_REDACTION="1"; $env:MYCELIA_AUTORESTORE="0"; python mycelia_platform.py'
```

Startet nur die Engine im Strict-Auditmodus.

Danach **keine Weboberfläche öffnen**, sondern den Random-Secret-Audit aus Abschnitt 15 ausführen.

---

## 34. Wichtige URLs

```text
http://127.0.0.1:8090/
```

Startseite

```text
http://127.0.0.1:8090/profile.php
```

Profil

```text
http://127.0.0.1:8090/forum.php
```

Forum

```text
http://127.0.0.1:8090/blogs.php
```

Blogs

```text
http://127.0.0.1:8090/my_blog.php
```

Mein Blog

```text
http://127.0.0.1:8090/admin.php
```

Admin-Panel

```text
http://127.0.0.1:8090/plugins.php
```

Plugin-Panel

```text
http://127.0.0.1:8090/privacy.php
```

Datenschutz-Center

---

## 35. Schnellbewertung der Strict-VRAM-Evidence

Die projektinterne Strict-VRAM-Sicherheitsbewertung gilt für einen Lauf als erfüllt, wenn das Evidence Bundle mindestens Folgendes zeigt:

```json
{
  "strict_vram_residency_claim": true,
  "negative_cpu_ram_probe": true,
  "last_restore_cpu_materialized": false,
  "strict_vram_certification_enabled": true
}
```

Wichtig:

- Das ist kein absoluter Unhackbarkeitsbeweis.
- Es ist ein reproduzierbarer Evidence-Gate für den geprüften Betriebszustand.
- Die Weboberfläche nutzt für Mutationen PHP-blinden Direct Ingest. PHP erhält dabei keine Formular-Klartexte. Die relevante Ausnahme ist der autorisierte DSGVO-Export „Eigene Daten herunterladen“, bei dem Klartext bewusst für den Nutzer erzeugt wird.
- Für den Strict-Audit keine Weboberfläche öffnen, bevor der Random-Secret-Probe abgeschlossen wurde.


---

## v1.20.1 Local Transport Token prüfen

```powershell
cd D:\web_sicherheit; Get-Content .\html\keys\local_transport.token
```

Zeigt den lokalen Transport-Token, den PHP und externe Tools automatisch als `X-Mycelia-Local-Token` an die Engine senden. Die Datei wird beim Engine-Start erzeugt.

## v1.20.1 Enterprise-Hardening-Status prüfen

```powershell
cd D:\web_sicherheit; $token = Get-Content .\html\keys\local_transport.token -Raw; $headers = @{ "Content-Type"="application/json"; "X-Mycelia-Local-Token"=$token.Trim() }; Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -Headers $headers -Body '{"command":"local_transport_security_status","payload":{}}'; Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -Headers $headers -Body '{"command":"native_library_authenticity","payload":{}}'
```

Prüft, ob `token_binding_enabled=true` und `fail_closed=true` gemeldet werden.


---

## 35. Medien in Forum, Blog und Blogposts testen

Ab Projektstand v1.21.21 können Bilder und sichere Medienlinks auch direkt bei der Blog-Erstellung verwendet werden.

### Forum-Medium anhängen

1. Webseite öffnen:

```powershell
Start-Process "http://127.0.0.1:8090/forum.php"
```

2. Thread erstellen oder vorhandenen Thread bearbeiten.
3. Unter **Medium anhängen** ein Bild auswählen oder einen sicheren Link eintragen.
4. Speichern.
5. Thread öffnen und prüfen, ob die Galerie sichtbar ist.

### Blog mit Medium erstellen

```powershell
Start-Process "http://127.0.0.1:8090/my_blog.php"
```

Dann:

1. Neuen Blog erstellen.
2. Titel und Beschreibung eintragen.
3. Bild oder sicheren Medienlink anhängen.
4. Speichern.
5. `Blogs` oder `Mein Blog` öffnen und prüfen, ob die Medienvorschau sichtbar ist.

### Blogpost mit Medium erstellen

1. In `Mein Blog` einen Blog auswählen.
2. Neuen Blogpost erstellen.
3. Optional Bild oder Medienlink anhängen.
4. Speichern.
5. Blogpost öffnen und Galerie prüfen.

Unterstützte Uploads:

```text
JPEG, PNG, GIF, WebP bis 3 MB
```

Unterstützte Links:

```text
YouTube, Vimeo, HTTPS-Bilder
```

---

## 36. Media-Diagnose bei leerer Anzeige

Wenn ein Bild oder Video nach dem Speichern nicht angezeigt wird, zuerst die Engine-Konsole prüfen.

### Fall A: Kein Media-Node gespeichert

Typisches Log:

```text
query_sql_like: Tabelle=mycelia_media_nodes Filter={...} Treffer=0
```

Bedeutung: Das Medium wurde beim Speichern nicht angelegt. Vorgehen:

```powershell
# Engine neu starten
cd D:\web_sicherheit\html
python mycelia_platform.py
```

```powershell
# PHP-Server neu starten
cd D:\web_sicherheit\www
php -S 127.0.0.1:8090
```

Dann im Browser:

```text
Strg + F5
```

Danach das Medium erneut anhängen. Alte fehlgeschlagene Uploadversuche können nicht nachträglich angezeigt werden, weil dabei kein `mycelia_media_nodes`-Eintrag entstanden ist.

### Fall B: Media-Node vorhanden, aber Browser zeigt nichts

Prüfen:

1. Ist der Upload kleiner als 3 MB?
2. Ist der MIME-Typ `image/jpeg`, `image/png`, `image/gif` oder `image/webp`?
3. Ist der Link HTTPS beziehungsweise YouTube/Vimeo?
4. Wurde die Seite hart neu geladen?
5. Gibt es Browser-Console-Fehler zu CSP, Data-URI oder Mixed Content?

---

## 37. Schneller Smoke-Test für Media-Regression

Nach dem Einspielen des v1.21.21-Stands:

```powershell
cd D:\web_sicherheit
python -m unittest discover -s tests -v
```

Für den gezielten Media-Test:

```powershell
cd D:\web_sicherheit
python -m unittest tests.test_media_attractor_system -v
```

Erwartung für den dokumentierten Fixstand:

```text
Ran 8 tests
OK
```


## v1.21.21 Hinweis zum PHP-blinden Betrieb

Für normale Mutationen im Forum, Blog, Mein Blog, Profil, Admin und bei Medienanhängen gilt: PHP soll keine Klartextfelder erhalten. Erwartet werden `sealed_ingest` und `direct_op`. Falls ein produktiver Klartext-POST akzeptiert wird, ist das ein Fehler im Zero-Logic-Gateway oder in der Formularbindung.

Ausnahme: Der DSGVO-Endpunkt **Eigene Daten herunterladen** erzeugt autorisierten Klartext für den angemeldeten Nutzer.

Prüfung im Browser/DevTools:

```text
POST-Body produktiver Mutationen: sealed_ingest + direct_op
Nicht erwartet: title=..., body=..., content=..., media_file_b64=... als Klartext im PHP-POST
```


## 45. Sicherheitsmodell richtig lesen

Die Härtungsprüfungen sind nicht als Liste offener Datenlecks zu verstehen. Im normalen Betrieb gilt:

- PHP bekommt keine produktiven Formular-, Forum-, Blog-, Medien- oder Admin-Klartexte.
- Mutationen laufen über `sealed_ingest` und `direct_op`.
- Engine-Sessions und Request-Tokens binden jede Mutation an eine geprüfte Sitzung.
- Logs, Memory-Probes und Native-Reports dienen dazu zu bestätigen, dass Fehlpfade keine nutzbaren Nutzdaten ausgeben.
- Der bewusste Klartext-Sonderfall ist **Datenschutz-Center → Eigene Daten herunterladen**.

Nach Änderungen an Security-, Session-, Upload- oder Native-Code sollten die Direct-Ingest-Tests, Web-Action-Token-Tests, Safe-Rendering-Tests und Memory-Probe-/Evidence-Kommandos erneut ausgeführt werden.


---

## 37. Nachrichten im Profil nutzen

Nach dem Login öffnest du das Profil:

```powershell
Start-Process "http://127.0.0.1:8090/profile.php#messages"
```

Dort befindet sich ab v1.21.21 das Nachrichtenmenü mit:

- Nachricht schreiben
- Inbox
- Outbox
- Lesen
- Antworten
- Löschen

---

## 38. E2EE-Schlüssel erzeugen

Jeder Nutzer, der Nachrichten empfangen soll, muss einmal einen E2EE-Schlüssel erzeugen und den Public Key registrieren.

Browser öffnen:

```powershell
Start-Process "http://127.0.0.1:8090/e2ee.php"
```

Dann im Browser:

```text
E2EE-Schlüssel im Browser erzeugen
Public Key registrieren
```

Der private Schlüssel bleibt browserseitig. Der Public Key wird als Mycelia-Attraktor gespeichert.

---

## 39. Nachricht schreiben

Im Profil unter `Nachrichten`:

1. Empfänger aus dem Verzeichnis auswählen.
2. Nachricht schreiben.
3. `Browserseitig verschlüsseln & senden` klicken.

Die Felder für Empfänger-Signatur und Public-Key-JWK müssen nicht mehr manuell kopiert werden.

---

## 40. Nachricht lesen

Im Profil unter `Inbox` oder `Outbox`:

1. Nachricht anklicken.
2. `Lesen` klicken.
3. Der Browser entschlüsselt lokal mit dem verfügbaren privaten Schlüssel.

PHP und Engine erhalten keinen Nachrichtenklartext.

---

## 41. Auf Nachricht antworten

In der Inbox:

1. Nachricht öffnen oder auswählen.
2. `Antworten` klicken.
3. Die Schreibmaske wird mit dem Absender als Empfänger befüllt.
4. Antwort schreiben und senden.

---

## 42. Nachricht löschen

In Inbox oder Outbox:

```text
Löschen
```

Das Löschen ist mailbox-seitig. Eine gelöschte Inbox-Nachricht verschwindet aus der eigenen Inbox, löscht aber nicht automatisch die Outbox-Kopie des Senders.

---

## 43. Nachrichten-Kompatibilitätsroute

Die Route

```powershell
Start-Process "http://127.0.0.1:8090/messages.php"
```

führt kompatibel zum Profil-Nachrichtenmenü:

```text
profile.php#messages
```


---

## Aktualisierung v1.21.14 bis v1.21.21

Diese Fassung dokumentiert die Entwicklungsschritte nach v1.21.13 bis zum aktuellen Stand **v1.21.21 Plugin Activation Hotfix**.

### v1.21.14 — Öffentlicher Blog-Katalog

Der Menüpunkt **Blogs** ist wieder ein öffentlicher Katalog. Session-gebundene Lesezugriffe setzen bei `list_blogs` keinen unbeabsichtigten `owner_signature`-Filter mehr. Dadurch sehen eingeloggte Nutzer auch Blogs anderer Nutzer. **Mein Blog** bleibt davon getrennt und zeigt weiterhin nur eigene Blogs.

### v1.21.15 — Blog-Kommentare und Blog-Reaktionen

Öffentliche Blogs können wieder kommentiert und mit Reaktionen versehen werden. Blog-Detailseiten zeigen Likes, Dislikes, Kommentare, Kommentarformulare sowie Kommentaraktionen. Die Engine behandelt `target_type = blog` korrekt als Blog-Kommentar-/Blog-Reaktionsziel.

### v1.21.16 — Trennung von öffentlicher Blog-Ansicht und Owner-Ansicht

Die öffentliche `Blogs`-Ansicht und die persönliche `Mein Blog`-Ansicht sind nun klar getrennt. `Blogs` bleibt öffentlich sichtbar, während `Mein Blog` explizit nach dem Besitzer filtert. Regressionstests prüfen, dass User B den Blog von User A im öffentlichen Katalog sieht.

### v1.21.17 — Enterprise User Plugins

Drei Enterprise-Plugins wurden ergänzt:

- **Mycelia Digest**: persönliche Aktivitätsübersicht mit E2EE-Zählern, neuen Kommentaren, Reaktionen und neuen öffentlichen Inhalten.
- **Privacy Guardian**: Dateninventur für eigene Inhalte, Medien, E2EE-Key-Status, Export-/Löschhinweise und Datenschutzstatus.
- **Content Trust & Safety Lens**: Trust-/Safety-Signale für öffentliche Inhalte auf Basis erlaubter Aggregate, ohne E2EE-Klartexte oder private Rohdaten.

Die Plugins laufen über ein kontrolliertes Plugin-Dashboard und erlaubte Capabilities. Sie lesen keine privaten E2EE-Nachrichten.

### v1.21.18 — Fun Plugins

Zehn Community-/Spaß-Plugins wurden ergänzt:

1. **Mycelia Achievements**
2. **Daily Pulse**
3. **Mycelia Quests**
4. **Reaction Stickers**
5. **Blog Mood Themes**
6. **Community Constellation**
7. **Sporenflug Random Discovery**
8. **Creator Cards**
9. **Polls / Abstimmungen**
10. **Time Capsules**

Dazu kamen neue Engine-Kommandos wie `fun_plugin_dashboard`, `create_poll`, `list_polls`, `vote_poll`, `create_time_capsule` und `list_time_capsules`.

### v1.21.19 — Plugin-Capabilities-Hotfix

Die Plugin-Capability-Allowlist wurde erweitert, damit die neuen Plugin-Templates installierbar sind. Ergänzt wurden sichere Capabilities wie `stats.own.content`, `stats.own.media`, `stats.own.e2ee_keys`, `stats.public.reactions` und `stats.public.blog.count`.

### v1.21.20 — Reaction Stickers und Blog Mood Themes im UI

Reaction Stickers wurden in Forum, Threads, Blogs, Blogposts und Kommentare integriert. Zusätzlich zu Like/Dislike können bei aktiviertem Plugin weitere Reaktionen genutzt werden:

- 🔥 Stark
- 😂 Lustig
- 💚 Herz
- 💡 Interessant
- ❤️ Danke
- 🤔 Nachdenklich

Blog Mood Themes sind bei Blog-Erstellung und Blog-Bearbeitung auswählbar, sofern das Plugin aktiv ist. Erlaubte Themes sind strikt allowlisted, etwa Security, Forschung, Gaming, Natur, Kreativ und Sci-Fi.

### v1.21.21 — Plugin Activation Hotfix

Plugin-Funktionen sind nun **inert by default**. Installierbare Plugin-Templates sind im Adminbereich sichtbar, aber ihre Funktionen werden erst freigeschaltet, wenn das jeweilige Plugin installiert und aktiviert wurde.

Konkret gilt:

- Ohne aktiviertes `reaction_stickers` bleiben nur Core-Reaktionen Like/Dislike sichtbar und serverseitig erlaubt.
- Ohne aktiviertes `blog_mood_themes` werden Blog-Theme-Felder nicht angezeigt und serverseitig ignoriert beziehungsweise blockiert.
- Polls und Time Capsules sind erst nach Aktivierung der jeweiligen Plugins nutzbar.
- Plugin-Dashboards zeigen nur aktivierte Plugin-Funktionen.
- Der Server erzwingt die Plugin-Aktivierung, die UI ist also nicht die einzige Schutzschicht.

Diese Änderung stellt sicher, dass Plugins dem erwarteten Enterprise-Modell folgen: **installieren, aktivieren, dann nutzen**.


## Zusatz: v1.21.21 Start- und Plugin-Prüfung

Nach dem Entpacken von v1.21.21:

```powershell
cd D:\web_sicherheit\html\native; powershell -ExecutionPolicy Bypass -File .\build_native_gpu_envelope.ps1 -Clean
```

```powershell
cd D:\web_sicherheit; python .\tools\generate_native_hash_manifest.py --project-root D:\web_sicherheit
```

```powershell
cd D:\web_sicherheit; python -m unittest discover -s tests -v
```

Für die normale Nutzung:

```powershell
cd D:\web_sicherheit\html; python mycelia_platform.py
```

```powershell
cd D:\web_sicherheit\www; php -S 127.0.0.1:8090
```

Plugins werden im Adminbereich installiert und aktiviert. Erst danach erscheinen abhängige UI-Funktionen wie Reaction Stickers, Blog Mood Themes, Polls und Time Capsules.
