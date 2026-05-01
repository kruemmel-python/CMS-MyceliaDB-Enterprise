# Dokumentation: MyceliaDB Strict-VRAM-Audit und Bewertung der implementierten Sicherheitsmechanismen

**Projekt:** MyceliaDB Enterprise / Web-Sicherheit  
**Ziel:** Bewertung, ob das System den konfigurierten Strict-VRAM-Evidence-Gate für eine prüfbare Strict-VRAM-Sicherheitsbewertung erfüllt  
**Stand:** Projektstand v1.21.25 mit Native-VRAM-Bridge, Strict Gate, klassifiziertem Memory-Probe, Scheduled Heartbeat Audit, Enterprise-Erweiterungen, Media-Attractor-System und E2EE-Profil-Mailbox
**Bewertung:** Der v1.20.1-Sicherheitsstand bleibt gültig; v1.21.25 ergänzt die Web-Content-Schicht um korrekt gespeicherte und gerenderte Bilder, Videos und sichere Medienlinks. Eine absolute Aussage wie „unhackbar“ bleibt fachlich nicht zulässig.

## 0.3 Präzisierung v1.21.25: abgesicherte Prüfzonen

Die Dokumentation vermeidet ab v1.21.25 pauschale Formulierungen wie „offene Angriffsflächen“ für Bereiche, die im Code bereits gehärtet sind. PHP ist ein blindes Gateway; die lokale API ist command- und sessiongebunden; Tokens rotieren; Logs müssen redigiert sein; Native-Bibliotheken werden authentifiziert; Memory-Probes unterscheiden sensiblen Klartext von public identifiers und nicht nutzbarem Envelope-Material. Restrisiko wird deshalb als prüfbarer Grenzfall formuliert: Gibt ein Fehlpfad verwertbare Nutzdaten aus, oder nur abgelehnte Requests, opaque Handles, redigierte Metadaten beziehungsweise verschlüsselte Pakete?


> Hinweis zu Sicherheitsformulierungen: Diese Dokumentation beschreibt die implementierten Schutzmechanismen und prüfbaren Evidenzpfade. Es wird keine prozentuale Sicherheitsfestlegung verwendet. Entscheidend sind die konkret umgesetzten Mechanismen: Zero-Logic-Gateway, Direct-Ingest, Native-VRAM-Pfade, Session-/Tokenbindung, Log-Redaction, Snapshot-Verschlüsselung, E2EE-Mailbox und prüfbare Auditberichte.

---

## 1. Kurzfazit

Die aktuelle MyceliaDB-Instanz hat im finalen Evidence-Lauf die technische Bedingung für den konfigurierten Strict-VRAM-Gate erfüllt:

```json
"strict_vram_residency_claim": true,
"negative_cpu_ram_probe": true,
"strict_hits": 0,
"strict_negative": true,
"last_restore_cpu_materialized": false,
"blockers": []
```

Damit wurde für diesen Lauf gezeigt:

- Die Engine lief im OpenCL-/Native-VRAM-Modus.
- Die Native GPU Residency Bridge war aktiv.
- Der letzte Snapshot-Restore war nicht CPU-materialisiert.
- Ein externer CPU-RAM-Probe wurde für die aktuelle Engine-PID eingereicht.
- Der Probe hatte keine strict-relevanten Treffer im Prozessspeicher.
- Das Strict Gate hat keine Blocker mehr gemeldet.
- Die Admin-/Console-Parität wurde hergestellt.

Professionell korrekt lautet die Aussage:

> MyceliaDB hat für den geprüften Evidence-Lauf die konfigurierte Strict-VRAM-Residency-Bedingung erfüllt. Die Plattform besteht damit die projektinterne Strict-VRAM-Sicherheitsbewertung für diesen Audit-Lauf, basierend auf Native-VRAM-Selftest, negativem externem CPU-RAM-Probe und nicht CPU-materialisiertem Restore.

Nicht korrekt wäre:

> MyceliaDB ist absolut unhackbar.

Mit v1.20 gilt zusätzlich:

> Der erfolgreiche Strict-VRAM-Evidence-Lauf wird nicht mehr als einmaliges Laborereignis behandelt, sondern durch einen Scheduled Heartbeat Audit, Native-Library-Authentizitätsprüfung, Local-Transport-Absicherung, Provenance Ledger und Quantum-DoS-Guard in einen wiederholbaren Enterprise-Betriebsprozess überführt.

---



## Korrektur v1.21.25: Keine PHP-Klartextannahme

Die Dokumentation unterscheidet jetzt schärfer zwischen klassischer Webangriffsfläche und der tatsächlich implementierten MyceliaDB-Webarchitektur. PHP erhält im Normalbetrieb keine Formular-, Forum-, Blog-, Medien- oder Admin-Klartexte. Diese Daten werden im Browser versiegelt und als `sealed_ingest` an die Engine weitergereicht. Das Zero-Logic-Gateway blockiert produktive Klartext-POSTs.

Die relevante Ausnahme ist der DSGVO-Endpunkt **„Eigene Daten herunterladen“**. Dort ist Klartextausgabe gewollt, weil der authentifizierte Nutzer seine eigenen Daten exportieren können muss.

Damit lautet die korrekte Sicherheitsbewertung: PHP bleibt als Gateway, Routing-, Session- und Transportkomponente prüfpflichtig, aber nicht als reguläre Klartext-Datenschicht. Sicherheitsprüfungen müssen sich daher auf Gateway-Allowlists, Session-/Tokenbindung, Localhost-API-Isolation, Log-Redaction, Datei-/Snapshotrechte, Native-Library-Authentizität und den bewusst autorisierten DSGVO-Export konzentrieren.

## 2. Ausgangsziel

Ziel war es, eine SQL-freie MyceliaDB-Plattform so weit abzusichern, dass nicht nur klassische Web-Sicherheitsmaßnahmen greifen, sondern auch eine strengere Hardware-Residency-Aussage geprüft werden kann.

Die Kernfrage lautete:

> Kann nachgewiesen werden, dass sensible Klartextwerte während des geprüften Betriebs nicht im CPU-RAM des MyceliaDB-Prozesses auftauchen, während Native-VRAM-Pfade aktiv sind?

Die Strict-VRAM-Sicherheitsbewertung wurde im Projekt nicht als mathematisch absolute Sicherheit verstanden, sondern als internes Evidence-Gate mit mehreren Bedingungen:

1. Native GPU Residency Bridge aktiv.
2. OpenCL/Core-GPU-Pfad aktiv.
3. Direct-GPU-Ingest bzw. Native Envelope aktiv.
4. Snapshot-/Restore-Pfad nicht CPU-materialisiert.
5. Externer RAM-Probe für aktuelle PID eingereicht.
6. RAM-Probe negativ für strict-relevante sensible Probes.
7. Keine Blocker im Strict-VRAM-Certification-Gate.
8. Admin-/Console-Auswertung stimmt mit Engine-Evidence überein.

---

## 3. Relevante Systemkomponenten

### 3.1 OpenCL Core Driver

Die Engine lief mit folgendem Driver-Modus:

```json
"driver_mode": "opencl:D:\\web_sicherheit\\build\\CC_OpenCl.dll+native-vram"
```

Bedeutung:

- `CC_OpenCl.dll` wurde aus dem Build-Ordner erkannt.
- OpenCL-Pfad ist aktiv.
- Zusätzlich wurde der Native-VRAM-Modus aktiviert.

### 3.2 Native GPU Residency Bridge

Die Native Bridge wurde aus folgendem Pfad geladen:

```text
D:\web_sicherheit\html\native\mycelia_gpu_envelope.dll
```

Die Bridge meldete unter anderem:

```json
"envelope_to_vram": true,
"snapshot_to_vram": true,
"native_command_executor": true,
"native_auth_executor": true,
"native_content_executor": true,
"native_admin_executor": true,
"native_plugin_executor": true,
"native_gdpr_executor": true,
"native_snapshot_runtime": true,
"native_persistence_mutation": true,
"native_strict_certification_gate": true,
"external_ram_probe_contract": true,
"gpu_resident_open_restore_proven": true
```

Damit waren die relevanten Hardware-/Native-Pfade vorhanden und aktiv.

### 3.3 Strict Gate

Das Strict Gate war aktiviert:

```json
"strict_vram_certification_enabled": true
```

Die Engine musste dafür mit mindestens folgendem Environment gestartet werden:

```powershell
cd D:\web_sicherheit\html
$env:MYCELIA_STRICT_VRAM_CERTIFICATION="1"
$env:MYCELIA_STRICT_RESPONSE_REDACTION="1"
$env:MYCELIA_AUTORESTORE="0"
python mycelia_platform.py
```

`MYCELIA_AUTORESTORE=0` war wichtig, um zu verhindern, dass ein Python-basierter Autorestore beim Start den Strict-Status blockiert.

---

## 4. Problemhistorie und Fehlerbilder

### 4.1 Früherer Blocker: `gpu_crypto_active: false`

Anfangs meldete der Report:

```json
"opencl_active": true,
"gpu_crypto_active": false,
"native_envelope_crypto_active": true
```

Das war ein Reporting-Problem. Die Native Envelope Bridge war aktiv, wurde aber nicht als GPU-Crypto gezählt.

Die korrigierte Logik lautet:

```python
gpu_crypto_active = core_gpu_crypto_active or native_envelope_crypto_active
```

Danach wurde korrekt gemeldet:

```json
"core_gpu_crypto_active": false,
"native_envelope_crypto_active": true,
"gpu_crypto_active": true
```

### 4.2 Früherer Blocker: fehlende `build\CC_OpenCl.dll`

Die Engine suchte unter anderem:

```text
D:\web_sicherheit\build\CC_OpenCl.dll
```

Der Build-Ordner fehlte zunächst. Nach dem Entpacken/Einfügen von `build\CC_OpenCl.dll` wurde der OpenCL-Core-Pfad korrekt erkannt.

### 4.3 Früherer Blocker: Python-materialisierter Restore

Ein Report zeigte:

```json
"last_restore_mode": "python_cpu_materialized",
"last_restore_cpu_materialized": true,
"strict_restore_residency_supported": false
```

Das blockierte die Strict-Zertifizierung. Ursache war ein Python-Restore-Pfad bzw. ein alter Restore-Audit-Pfad.

Der saubere Lauf wurde mit deaktiviertem Autorestore ausgeführt:

```powershell
$env:MYCELIA_AUTORESTORE="0"
```

Im finalen erfolgreichen Report stand dann:

```json
"last_restore_mode": "none",
"last_restore_cpu_materialized": false
```

### 4.4 Früherer Blocker: externe Memory-Probe fehlte

Das Strict Gate meldete zunächst:

```json
"No negative external CPU-RAM memory probe has been submitted for the current MyceliaDB PID."
```

Dieser Blocker wurde behoben, indem der externe RAM-Probe erzeugt und an die Engine übergeben wurde.

### 4.5 Früherer Blocker: Admin-/Console-Parität

Das Admin-Panel zeigte zeitweise andere Ergebnisse als die Konsole. Es wurde deshalb ein synchronisiertes Evidence Bundle eingeführt:

```json
"admin_console_parity": {
  "single_source_of_truth": "strict_vram_evidence_bundle",
  "matches_console_tools_after_probe_submission": true
}
```

Damit ist `strict_vram_evidence_bundle` die zentrale Quelle für Admin- und Console-Bewertung.

---

## 5. Erste Probe-Läufe mit realen Testwerten

### 5.1 Probe mit `Leipzig`, `Krümmel` und Signatur

Ausgeführt wurde sinngemäß:

```powershell
cd D:\web_sicherheit

$manifest = Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"residency_audit_manifest","payload":{}}'

python D:\web_sicherheit\tools\mycelia_memory_probe.py `
  --pid $manifest.pid `
  --challenge-id $manifest.challenge_id `
  --probe-sensitive "Leipzig" `
  --probe-sensitive "Krümmel" `
  --probe-public "4166bbf4b6c623571001321d8721b576d023c9f2299624370d2e12d1df56caf9" `
  --json-out D:\web_sicherheit\residency_probe.json
```

Ergebnis in einem der Zwischenläufe:

```json
"hits": 1,
"strict_hits": 1,
"negative": false,
"strict_negative": false,
"hit_counts_by_kind": {
  "sensitive_cleartext": 1
}
```

Der Treffer war:

```json
"probe_kind": "sensitive_cleartext",
"encoding": "utf-16le",
"encoding_bytes": 14
```

Das entsprach sehr wahrscheinlich `Krümmel` als UTF-16LE.

### 5.2 Signaturen als Public Identifier

Die lange Signatur:

```text
4166bbf4b6c623571001321d8721b576d023c9f2299624370d2e12d1df56caf9
```

wurde als `public_identifier` klassifiziert:

```json
"probe_kind": "public_identifier",
"strict_relevant": false
```

Damit blockierten Signaturtreffer die Strict-Zertifizierung nicht mehr. Das ist korrekt, weil Signaturen operative Handles sind und nicht mit sensiblen Profilklartexten gleichgesetzt werden.

---

## 6. Klassifizierter Memory-Probe

Das Memory-Probe-Tool wurde in Version 2 klassifiziert:

```json
"scanner_version": "MYCELIA_CPU_RAM_PROBE_V2_CLASSIFIED"
```

Relevante Felder:

```json
"probe_kind": "sensitive_cleartext",
"strict_relevant": true
```

oder:

```json
"probe_kind": "public_identifier",
"strict_relevant": false
```

Wichtige Ergebnisfelder:

| Feld | Bedeutung |
|---|---|
| `hits` | alle Treffer |
| `strict_hits` | strict-relevante Treffer |
| `non_strict_hits` | nicht blockierende Treffer |
| `negative` | keine Treffer insgesamt |
| `strict_negative` | keine strict-relevanten Treffer |
| `raw_negative` | keine Roh-Treffer |
| `hit_counts_by_kind` | Treffer nach Klassifikation |

Für die Strict-VRAM-Bewertung ist `strict_hits` entscheidend, nicht pauschal `hits`.

---

## 7. Projektdatei-Suche nach `Krümmel`

Um zu prüfen, ob `Krümmel` als Altlast im Projekt vorhanden ist, wurden folgende Befehle ausgeführt:

```powershell
cd D:\web_sicherheit

Get-ChildItem D:\web_sicherheit -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -lt 50MB } |
  Select-String -SimpleMatch "Krümmel" -ErrorAction SilentlyContinue |
  Select-Object Path, LineNumber, Line
```

Ergebnis:

```text
D:\web_sicherheit\ENTERPRISE_WWW_README.md
D:\web_sicherheit\neue_analysen.txt
D:\web_sicherheit\strict_kruemmel_probe.txt
D:\web_sicherheit\strict_probes.txt
D:\web_sicherheit\whitepaper.md
D:\web_sicherheit\tests\test_autosnapshot_persistence.py
D:\web_sicherheit\tests\test_residency_external_probe.py
D:\web_sicherheit\tests\test_snapshot_residency.py
D:\web_sicherheit\tools\mycelia_memory_probe.py
```

Zusätzlich:

```powershell
Get-ChildItem D:\web_sicherheit -Recurse -File -Include *.log,*.json,*.txt,*.md,*.php,*.py,*.mycelia -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -lt 50MB } |
  Select-String -SimpleMatch "Krümmel" -ErrorAction SilentlyContinue |
  Select-Object Path, LineNumber, Line
```

Ergebnis ebenfalls mit Treffern in Tests, README, Whitepaper und Probe-Dateien.

Interpretation:

> `Krümmel` ist als Test-/Dokumentationswert im Projektbestand kontaminiert und daher kein idealer finaler Strict-Probe-Wert.

---

## 8. Kontrolltest mit frischem Random-Secret

Zur Vermeidung kontaminierter Altwerte wurde ein neuer, noch nie im System gespeicherter Wert erzeugt:

```powershell
cd D:\web_sicherheit
$secret = "VRAM_ONLY_" + [guid]::NewGuid().ToString("N")
[System.IO.File]::WriteAllLines("D:\web_sicherheit\strict_random_probe.txt", @($secret), [System.Text.UTF8Encoding]::new($false))
Write-Host "SECRET=$secret"
```

Konkreter Wert aus dem Lauf:

```text
VRAM_ONLY_d1ad505ea4444d95965dfa273d9d3632
```

Dann wurde der Probe ausgeführt:

```powershell
$manifest = Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"residency_audit_manifest","payload":{}}'

python D:\web_sicherheit\tools\mycelia_memory_probe.py `
  --pid $manifest.pid `
  --challenge-id $manifest.challenge_id `
  --probe-file D:\web_sicherheit\strict_random_probe.txt `
  --json-out D:\web_sicherheit\residency_probe_random.json
```

Ergebnis:

```json
{
  "status": "ok",
  "scanner_version": "MYCELIA_CPU_RAM_PROBE_V2_CLASSIFIED",
  "pid": 23544,
  "challenge_id": "4542a8c97370559c1ca6d85cbb53dc33",
  "hits": 0,
  "strict_hits": 0,
  "non_strict_hits": 0,
  "negative": true,
  "strict_negative": true,
  "raw_negative": true,
  "scanned_regions": 778,
  "scanned_bytes": 894799872,
  "findings": [],
  "evidence_digest": "7b080d91dd13b52351776475dd381025116baefa257f68b77eb238390cdb0a79"
}
```

Das ist der entscheidende negative externe RAM-Probe.

---

## 9. Gegenprobe mit `Krümmel`

Zum Vergleich wurde eine separate Probe-Datei für `Krümmel` erzeugt:

```powershell
[System.IO.File]::WriteAllLines("D:\web_sicherheit\strict_kruemmel_probe.txt", @("Krümmel"), [System.Text.UTF8Encoding]::new($false))

$manifest = Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"residency_audit_manifest","payload":{}}'

python D:\web_sicherheit\tools\mycelia_memory_probe.py `
  --pid $manifest.pid `
  --challenge-id $manifest.challenge_id `
  --probe-file D:\web_sicherheit\strict_kruemmel_probe.txt `
  --json-out D:\web_sicherheit\residency_probe_kruemmel.json
```

Ergebnis:

```json
{
  "hits": 1,
  "strict_hits": 1,
  "negative": false,
  "strict_negative": false,
  "hit_counts_by_kind": {
    "sensitive_cleartext": 1
  },
  "findings": [
    {
      "probe_kind": "sensitive_cleartext",
      "strict_relevant": true,
      "encoding": "utf-16le",
      "encoding_bytes": 14
    }
  ]
}
```

Interpretation:

> `Krümmel` bleibt als UTF-16LE-Altlast im Prozessspeicher auffindbar und ist als finaler Sicherheits-Probe ungeeignet, weil der Wert im Projektbestand, in Tests und in Dokumentation mehrfach vorhanden ist.

Wichtig: Der Random-Secret-Test zeigt trotzdem, dass ein neuer, nicht vorbelasteter sensibler Wert im geprüften Lauf nicht im CPU-RAM der Engine gefunden wurde.

---

## 10. Einreichen des negativen Random-Probe-Reports

Der negative Random-Probe wurde an die Engine übergeben:

```powershell
$report = Get-Content D:\web_sicherheit\residency_probe_random.json -Raw

$body = @{
  command = "submit_external_memory_probe"
  payload = ($report | ConvertFrom-Json)
} | ConvertTo-Json -Depth 20

Invoke-RestMethod `
  -Uri "http://127.0.0.1:9999/" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Die Engine akzeptierte den Report:

```text
status external_memory_probe
------ ---------------------
ok     @{status=accepted; audit_version=MYCELIA_CPU_RAM_PROBE_V2_CLASSIFIED; classification_version=MYCELIA_PROBE_CL...
```

---

## 11. Finales Evidence Bundle

Danach wurde das Evidence Bundle abgefragt:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:9999/" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"command":"strict_vram_evidence_bundle","payload":{}}' |
  ConvertTo-Json -Depth 30
```

Die relevante finale Passage:

```json
{
  "status": "ok",
  "pid": 23544,
  "driver_mode": "opencl:D:\\web_sicherheit\\build\\CC_OpenCl.dll+native-vram",
  "strict_vram_certification_enabled": true,
  "negative_cpu_ram_probe": true,
  "last_restore_mode": "none",
  "last_restore_cpu_materialized": false,
    "admin_console_parity": {
    "single_source_of_truth": "strict_vram_evidence_bundle",
    "matches_console_tools_after_probe_submission": true
  }
}
```

Die `strict_vram_certification` meldete:

```json
{
    "strict_vram_residency_claim": true,
  "strict_vram_certification_enabled": true,
  "negative_cpu_ram_probe": true,
  "process_pid": 23544,
  "blockers": [],
  "conclusion": "Strict VRAM residency is supported by the configured evidence gate."
}
```

Das ist der finale grüne Zustand.

---

## 12. Vollständiger PowerShell-Audit-Ablauf

### 12.1 Engine starten

```powershell
cd D:\web_sicherheit\html
$env:MYCELIA_STRICT_VRAM_CERTIFICATION="1"
$env:MYCELIA_STRICT_RESPONSE_REDACTION="1"
$env:MYCELIA_AUTORESTORE="0"
python mycelia_platform.py
```

### 12.2 Random-Secret erzeugen

```powershell
cd D:\web_sicherheit
$secret = "VRAM_ONLY_" + [guid]::NewGuid().ToString("N")
[System.IO.File]::WriteAllLines("D:\web_sicherheit\strict_random_probe.txt", @($secret), [System.Text.UTF8Encoding]::new($false))
Write-Host "SECRET=$secret"
```

### 12.3 Manifest holen und Memory-Probe ausführen

```powershell
$manifest = Invoke-RestMethod `
  -Uri "http://127.0.0.1:9999/" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"command":"residency_audit_manifest","payload":{}}'

python D:\web_sicherheit\tools\mycelia_memory_probe.py `
  --pid $manifest.pid `
  --challenge-id $manifest.challenge_id `
  --probe-file D:\web_sicherheit\strict_random_probe.txt `
  --json-out D:\web_sicherheit\residency_probe_random.json
```

### 12.4 Report an Engine übergeben

```powershell
$report = Get-Content D:\web_sicherheit\residency_probe_random.json -Raw

$body = @{
  command = "submit_external_memory_probe"
  payload = ($report | ConvertFrom-Json)
} | ConvertTo-Json -Depth 20

Invoke-RestMethod `
  -Uri "http://127.0.0.1:9999/" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### 12.5 Evidence Bundle abrufen

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:9999/" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"command":"strict_vram_evidence_bundle","payload":{}}' |
  ConvertTo-Json -Depth 30
```

### 12.6 Erwartete grüne Werte

```json
{
  "strict_vram_certification_enabled": true,
  "negative_cpu_ram_probe": true,
  "last_restore_cpu_materialized": false,
    "strict_vram_residency_claim": true,
  "blockers": []
}
```

---

## 13. Sicherheitsbewertung

### 13.1 Erreicht

| Kriterium | Ergebnis |
|---|---:|
| OpenCL Core Driver aktiv | ja |
| Native-VRAM Bridge aktiv | ja |
| `gpu_crypto_active` | ja |
| Native Envelope-to-VRAM | ja |
| Native Snapshot Runtime | ja |
| Strict Gate aktiviert | ja |
| Externer Memory-Probe eingereicht | ja |
| Random-Secret-Probe negativ | ja |
| Strict-relevante Treffer | 0 |
| Letzter Restore CPU-materialisiert | nein |
| Admin-/Console-Parität | ja |
| Strict-VRAM-Gate | erfüllt |

### 13.2 Nicht als absolut bewiesen

Folgende Aussagen sind weiterhin nicht seriös:

- „Unhackbar“
- „für alle zukünftigen Daten garantiert“
- „formal bewiesene absolute VRAM-only-Datenbank“
- „kein Angreifer kann jemals Daten auslesen“

Warum?

- Der Nachweis gilt für den konkreten Audit-Lauf.
- Neue Codepfade, neue Plugins, neue UI-Antworten oder neue Restore-Pfade können neue Materialisierung erzeugen.
- Betriebssystem-, Treiber- und Hardwareverhalten bleiben externe Vertrauensanker.
- Export- und Profilanzeigefunktionen können autorisiert Klartext materialisieren, wenn sie bewusst genutzt werden.
- Ein RAM-Probe ist forensische Evidenz, aber kein mathematischer Vollbeweis.

### 13.3 Professionell korrekte Aussage

> MyceliaDB erreicht im geprüften Lauf die projektinterne Strict-VRAM-Sicherheitsbewertung: Native-VRAM-Pfade sind aktiv, der Snapshot-Restore war nicht CPU-materialisiert, ein externer RAM-Probe für ein frisches sensibles Secret war negativ, und das Strict Gate meldete keine Blocker.

---

## 14. Bewertung von `Krümmel`

`Krümmel` wurde mehrfach in Projektdateien gefunden:

- Tests
- README
- Whitepaper
- Probe-Dateien
- Analyse-Dateien
- Tool-Dokumentation

Daher ist `Krümmel` ein kontaminierter Probe-Wert. Er eignet sich nicht mehr als finaler Strict-Probe, weil er nicht eindeutig einem aktuellen Engine-Leak zugeordnet werden kann.

Die Gegenprobe ist trotzdem nützlich:

- Sie zeigt, dass der Scanner echte UTF-16LE-Reste findet.
- Sie zeigt, dass der Probe nicht blind grün meldet.
- Sie zeigt, dass Altwerte separat behandelt werden müssen.

Aber für die finale Strict-VRAM-Bewertung wurde korrekt der frische Random-Wert verwendet.

---

## 15. Empfehlung für zukünftige Audits

Für jeden neuen Audit-Lauf sollte ein neuer Random-Probe verwendet werden:

```powershell
$secret = "VRAM_ONLY_" + [guid]::NewGuid().ToString("N")
```

Dieser Wert darf:

- nicht im Quellcode stehen,
- nicht in README/Whitepaper stehen,
- nicht in Testdateien stehen,
- nicht in Logs stehen,
- nicht als PowerShell-Literal im eigentlichen Probe-Befehl auftauchen,
- nur in einer temporären UTF-8-No-BOM-Probe-Datei stehen,
- nach dem Audit gelöscht werden.

Empfohlen:

```powershell
Remove-Item D:\web_sicherheit\strict_random_probe.txt -Force
Remove-Item D:\web_sicherheit\residency_probe_random.json -Force
```

Falls der Report archiviert wird, sollte er nur Hashes und Summary enthalten, nicht das Secret.

---

## 16. Abschlussbewertung

Der finale Evidence-Lauf erfüllt die definierte Strict-VRAM-Sicherheitsbedingung:

```text
Native VRAM Bridge: GRÜN
OpenCL Core: GRÜN
Strict Gate: GRÜN
External RAM Probe: GRÜN
Random Secret: GRÜN
Python-Restore-Blocker: GRÜN
Admin-/Console-Parität: GRÜN
Strict-VRAM: GRÜN
```

Die korrekte Endaussage lautet:

> Für den geprüften Lauf hat MyceliaDB die konfigurierte Strict-VRAM-Residency-Prüfung bestanden. Das System besteht damit die projektinterne Strict-VRAM-Sicherheitsbewertung auf Basis eines negativen externen CPU-RAM-Probes, aktiver Native-VRAM-Pfade und eines nicht CPU-materialisierten Restore-Zustands.

Die fachlich saubere Einschränkung lautet:

> Diese Bewertung ist eine reproduzierbare technische Evidence-Aussage für den konkreten geprüften Betriebszustand, kein absoluter Unhackbarkeitsbeweis.


---

## 17. Update v1.20: Enterprise-Sicherheits- und Skalierungsstufe

Projektstand **v1.20** erweitert die bisherige Strict-VRAM-Residency-Dokumentation um sechs Enterprise-Funktionen. Diese Funktionen ersetzen den Strict-VRAM-Evidence-Lauf nicht, sondern stabilisieren dessen Betriebsumgebung.

Die neue Bewertung lautet:

```text
Strict-VRAM-Evidence-Lauf: GRÜN, wenn Random-Secret-Probe negativ ist
Scheduled Heartbeat Audit: wiederholbare laufende Prüfung
Native Library Authenticity: reduziert DLL-Hijacking-Risiko
Local Transport Security: reduziert Localhost-Proxying/MITM-Risiko
Provenance Ledger: auditierbare Mutationskette
SMQL: strukturierte + semantische Abfragen
Föderation: skalierbarer Influx statt blindem State-Overwrite
Quantum Guard: Schutz gegen Cognitive/Quantum-DoS
```

Wichtig: Die Strict-VRAM-Bewertung bleibt weiterhin an den konkreten Audit-Zustand gebunden. v1.20 macht die Beweiskette aber wiederholbarer, besser überwachbar und robuster gegen Enterprise-relevante Angriffsklassen.

---

## 18. Scheduled Heartbeat Audit

Der manuelle Random-Secret-Probe wurde in v1.19.9/v1.20 in einen wiederholbaren Heartbeat-Audit überführt.

### 18.1 Zweck

Der Heartbeat Audit prüft regelmäßig, ob der konfigurierte Strict-VRAM-Evidence-Gate weiterhin erfüllbar ist:

1. Engine erzeugt Audit-Manifest mit PID und Challenge-ID.
2. Externes Tool erzeugt frisches Random-Secret.
3. `mycelia_memory_probe.py` scannt den Prozessspeicher der Engine.
4. Report wird an die Engine übermittelt.
5. Engine erzeugt `strict_vram_evidence_bundle`.
6. Ergebnis wird signiert.
7. Admin-Dashboard zeigt den Hardware-Residency-Status.

### 18.2 Einmallauf

```powershell
cd D:\web_sicherheit
powershell -ExecutionPolicy Bypass -File .\tools\run_heartbeat_audit.ps1 -ProjectRoot D:\web_sicherheit -Engine http://127.0.0.1:9999/
```

### 18.3 Scheduled Task installieren

```powershell
cd D:\web_sicherheit
powershell -ExecutionPolicy Bypass -File .\tools\install_heartbeat_audit_task.ps1 -ProjectRoot D:\web_sicherheit -Engine http://127.0.0.1:9999/ -At 03:15
```

### 18.4 Erwartetes Dashboard-Ergebnis

```text
Aktueller Hardware-Residency-Status: ZERTIFIZIERT
```

Der Status darf nur grün sein, wenn im Evidence Bundle mindestens gilt:

```json
{
    "strict_vram_residency_claim": true,
  "negative_cpu_ram_probe": true,
  "last_restore_cpu_materialized": false,
  "blockers": []
}
```

### 18.5 Sicherheitsgrenze

Der Heartbeat Audit ist ein externer Notar-Prozess. Er ersetzt keine absolute Sicherheit, verhindert aber, dass die Plattform sich ausschließlich selbst zertifiziert.

---

## 19. Native Library Authenticity und DLL-Hijacking-Prävention

### 19.1 Problem

Die VRAM-Sicherheitsbehauptung hängt an nativen Komponenten:

```text
D:\web_sicherheit\build\CC_OpenCl.dll
D:\web_sicherheit\html\native\mycelia_gpu_envelope.dll
```

Wenn eine dieser DLLs durch eine Proxy-/Hijacking-DLL ersetzt würde, könnte der externe RAM-Probe unter Umständen zu spät kommen.

### 19.2 v1.20-Lösung

v1.20 führt ein Native-Hash-Manifest ein:

```text
docs/native_library_hashes.json
```

Vor dem Laden via `ctypes.CDLL` berechnet die Engine den SHA-256 der jeweiligen Library und vergleicht ihn mit dem Manifest. Bei Abweichung wird die Library nicht geladen.

### 19.3 Manifest erzeugen

```powershell
cd D:\web_sicherheit
python .\tools\generate_native_hash_manifest.py
```

Nach einem Native-Build:

```powershell
cd D:\web_sicherheit\html\native
.\build_native_gpu_envelope.ps1 -Clean
```

### 19.4 Status prüfen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"native_library_authenticity","payload":{}}' | ConvertTo-Json -Depth 20
```

Erwartung:

```json
{
  "status": "ok",
  "core_opencl_driver": {
    "verified": true
  },
  "native_gpu_envelope": {
    "verified": true
  }
}
```

### 19.5 Auswirkung auf Strict-VRAM-Sicherheit

Diese Prüfung ist kein RAM-Residency-Beweis, aber eine notwendige Vorbedingung für Vertrauen in den Native-Pfad. Ohne authentische DLLs ist eine Sicherheitsaussage nicht belastbar.

---

## 20. Localhost Transport Security

### 20.1 Problem

Die PHP-Weboberfläche kommuniziert mit der Engine lokal über:

```text
http://127.0.0.1:9999/
```

Auch wenn die Nutzdaten versiegelt sind, können lokale Metadaten wie Command-Namen, Session-Handles oder Control-Requests relevant sein.

### 20.2 v1.20-Lösung

v1.20 führt lokale Transport-Bindung ein:

```text
html/keys/local_transport.token
Header: X-Mycelia-Local-Token
```

PHP sendet den Token bei Engine-Requests. Die Engine akzeptiert Control-Requests nur mit passendem Token.

Optional kann lokales HTTPS aktiviert werden:

```powershell
$env:MYCELIA_LOCAL_HTTPS="1"
```

Zertifikate können erzeugt werden mit:

```powershell
cd D:\web_sicherheit
python .\tools\generate_localhost_tls.py
```

### 20.3 Status prüfen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"local_transport_security_status","payload":{}}' | ConvertTo-Json -Depth 20
```

### 20.4 Auswirkung auf Strict-VRAM-Sicherheit

Local Transport Security schützt nicht direkt den VRAM, reduziert aber Localhost-MITM-, Port-Proxying- und Control-Plane-Manipulationsrisiken.

---

## 21. Cryptographic Data Lineage / Provenance Ledger

### 21.1 Zweck

Die bisherige Datenhaltung konnte zeigen, dass Daten nicht klassisch in SQL liegen. Für Enterprise-Audits reicht das nicht: Es muss nachvollziehbar sein, wer was wann verändert hat.

v1.20 ergänzt ein Append-only Provenance Ledger:

```text
html/snapshots/provenance.mycelia
```

Jede relevante Mutation erzeugt ein verkettetes Ereignis mit:

- vorherigem Ledger-Hash,
- Actor-Signatur,
- Operation,
- betroffener Attraktor-Signatur,
- Zeitstempel,
- neuem Event-Hash.

### 21.2 Befehle

Provenance prüfen:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"provenance_verify","payload":{}}' | ConvertTo-Json -Depth 20
```

Provenance-Log anzeigen:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"provenance_log","payload":{"limit":20}}' | ConvertTo-Json -Depth 20
```

### 21.3 Bewertung

Das Ledger stärkt Non-Repudiation und Auditierbarkeit. Es ersetzt nicht die VRAM-Residency-Prüfung, ergänzt aber die Enterprise-Aussage um Datenherkunft und Änderungsnachweis.

---

## 22. Semantic Mycelia Query Language / SMQL

### 22.1 Zweck

SMQL verbindet deterministische Filter mit assoziativen Mycelia-Cues.

Beispiel:

```text
FIND mycelia_users WHERE role=admin ASSOCIATED WITH "High Security" LIMIT 10
```

SMQL ersetzt nicht SQL. Es ist eine kontrollierte Query-Sprache über Mycelia-Attraktoren.

### 22.2 Befehle

SMQL erklären:

```powershell
$body = @{
  command = "smql_explain"
  payload = @{
    query = 'FIND mycelia_users WHERE role=admin ASSOCIATED WITH "High Security" LIMIT 10'
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 20
```

SMQL ausführen:

```powershell
$body = @{
  command = "smql_query"
  payload = @{
    query = 'FIND mycelia_users WHERE role=admin ASSOCIATED WITH "High Security" LIMIT 10'
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 20
```

### 22.3 Sicherheitsgrenze

SMQL darf keine freie Codeausführung, keine SQL-Durchleitung und keine Rohgraph-Scans erlauben. Es ist ein deterministisch begrenzter Query-Compiler in Mycelia-Operationen.

---

## 23. Myzel-Föderation

### 23.1 Zweck

MyceliaDB war ursprünglich eine einzelne Engine-/GPU-Instanz. v1.20 führt Föderationsmechanismen ein, ohne einen Remote-State direkt blind zu überschreiben.

Föderation bedeutet hier:

```text
Remote stable attractors
→ signierter/vertrauenswürdiger Export
→ lokaler Influx
→ mycelia_federated_influx
→ lokale Assimilation
```

### 23.2 Befehle

Status:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"federation_status","payload":{}}' | ConvertTo-Json -Depth 20
```

Peer hinzufügen:

```powershell
$body = @{
  command = "federation_peer_add"
  payload = @{
    peer_id = "node-b"
    endpoint = "https://127.0.0.1:10099/"
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 20
```

Stabile Attraktoren exportieren:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"federation_export_stable","payload":{"limit":50}}' | ConvertTo-Json -Depth 30
```

Synchronisationstool:

```powershell
cd D:\web_sicherheit
python .\tools\mycelia_federation_sync.py --engine http://127.0.0.1:9999/
```

### 23.3 Split-Brain-Schutz

Remote-Daten werden nicht als autoritativer State importiert. Sie werden als exogener Nährstoff-Influx behandelt. Das reduziert State-Konflikte und erhält lokale Autorität.

---

## 24. Cognitive DoS / Quantum Oracle Guard

### 24.1 Problem

Ein Angreifer oder ein kompromittiertes Plugin könnte versuchen, hohe Dissonanz/Tension zu erzeugen, um GPU-intensive Quantum-/VQE-Pfade zu triggern.

### 24.2 v1.20-Lösung

v1.20 führt Cooldown und Token-Bucket ein:

```powershell
$env:MYCELIA_QUANTUM_INTUITION_COOLDOWN_MS="60000"
$env:MYCELIA_QUANTUM_INTUITION_BURST="1"
```

Der Guard verhindert, dass Quantum-Intuition beliebig oft pro Zeiteinheit ausgelöst wird.

### 24.3 Status prüfen

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"quantum_guard_status","payload":{}}' | ConvertTo-Json -Depth 20
```

### 24.4 Bewertung

Der Quantum Guard ist für Verfügbarkeit und GPU-Ressourcenschutz relevant. Er ist kein Datenresidenzbeweis, aber ein wichtiger Schutz gegen Cognitive Denial of Service.

---

## 25. Empfohlener v1.20-Startablauf

### 25.1 Normaler Webbetrieb

```powershell
cd D:\web_sicherheit\html
python mycelia_platform.py
```

```powershell
cd D:\web_sicherheit\www
php -S 127.0.0.1:8090
```

Der Webbetrieb darf Klartext anzeigen, weil Nutzer Inhalte sehen müssen. Dieser Pfad ist getrennt vom Strict-VRAM-Audit.

### 25.2 Strict-Audit-Betrieb

```powershell
cd D:\web_sicherheit\html
$env:MYCELIA_STRICT_VRAM_CERTIFICATION="1"
$env:MYCELIA_STRICT_RESPONSE_REDACTION="1"
$env:MYCELIA_AUTORESTORE="0"
python mycelia_platform.py
```

Dann keine Weboberfläche öffnen. Der Audit erfolgt über externes Tool oder Heartbeat.

### 25.3 Manueller Random-Secret-Audit

```powershell
cd D:\web_sicherheit

$secret = "VRAM_ONLY_" + [guid]::NewGuid().ToString("N")
[System.IO.File]::WriteAllLines("D:\web_sicherheit\strict_random_probe.txt", @($secret), [System.Text.UTF8Encoding]::new($false))

$manifest = Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"residency_audit_manifest","payload":{}}'

python D:\web_sicherheit\tools\mycelia_memory_probe.py --pid $manifest.pid --challenge-id $manifest.challenge_id --probe-file D:\web_sicherheit\strict_random_probe.txt --json-out D:\web_sicherheit\residency_probe_random.json

$report = Get-Content D:\web_sicherheit\residency_probe_random.json -Raw

$body = @{
  command = "submit_external_memory_probe"
  payload = ($report | ConvertFrom-Json)
} | ConvertTo-Json -Depth 20

Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body $body

Invoke-RestMethod -Uri "http://127.0.0.1:9999/" -Method Post -ContentType "application/json" -Body '{"command":"strict_vram_evidence_bundle","payload":{}}' | ConvertTo-Json -Depth 30
```

### 25.4 Erfolgsbedingungen

```json
{
    "strict_vram_residency_claim": true,
  "negative_cpu_ram_probe": true,
  "last_restore_cpu_materialized": false,
  "blockers": []
}
```

---

## 26. v1.20-Abschlussbewertung

Die projektinterne Strict-VRAM-Sicherheitsbewertung bleibt definiert als erfüllter Strict-VRAM-Evidence-Gate für einen konkreten Betriebszustand.

v1.20 verbessert diese Aussage durch zusätzliche Betriebssicherungen:

| Bereich | Wirkung auf Sicherheitsaussage |
|---|---|
| Scheduled Heartbeat Audit | macht die Prüfung wiederholbar und dashboardfähig |
| Native Library Authenticity | verhindert leichtes DLL-Hijacking der Vertrauenskette |
| Local Transport Security | schützt lokale Control Plane gegen Proxying/MITM |
| Provenance Ledger | dokumentiert Mutationen kryptografisch |
| SMQL | ermöglicht kontrollierte strukturierte/semantische Abfragen |
| Föderation | skaliert Wissen als Influx statt State-Overwrite |
| Quantum Guard | schützt GPU vor Dissonanz-/Oracle-DoS |

Die finale, fachlich belastbare Aussage lautet:

> MyceliaDB v1.20 erreicht die projektinterne Strict-VRAM-Sicherheitsbewertung, wenn der Strict-VRAM-Evidence-Gate mit frischem Random-Secret-Probe erfolgreich ist und das Heartbeat-/Dashboard-Bundle `negative_cpu_ram_probe=true`, `last_restore_cpu_materialized=false` und keine Blocker meldet.

Die weiterhin notwendige Einschränkung lautet:

> Dies ist ein reproduzierbarer technischer Sicherheitsnachweis für den geprüften Betriebszustand. Es ist kein absoluter Beweis für Unhackbarkeit und keine allgemeine Zertifizierung gegen alle lokalen, physischen oder Supply-Chain-Angriffe.


---

## Ergänzung v1.20.1: Perfekter Enterprise-Hardening-Status

Die Admin-Auswertung zeigte nach v1.20 drei Restpunkte: Localhost-Transport war noch nicht tokengebunden, Native-Library-Authenticity zeigte die Fail-Closed-Policy nicht eindeutig und Admin-/SMQL-Debug-Reports enthielten zu viele interne Felder. Diese Punkte wurden in v1.20.1 korrigiert.

### Erwartete Statuswerte

```json
{
  "local_transport_security_status": {
    "token_binding_enabled": true
  },
  "native_library_authenticity": {
    "checks": [
      {
        "fail_closed": true,
        "fail_closed_triggered": false
      }
    ]
  }
}
```

### Admin-Report-Redaction

Das Admin-Dashboard zeigt keine Credential- oder Transport-Secrets mehr. Insbesondere werden folgende Felder aus Dashboard-JSON entfernt oder gekürzt:

```text
auth_pattern
profile_seed
profile_blob
content_seed
content_blob
request_token
sealed_ingest
vollständige engine_session
vollständige Signaturen
```

### SMQL Safe Mode

SMQL-Abfragen laufen standardmäßig im Safe-Modus:

```json
{
  "safe_mode": true,
  "redaction_policy": "enterprise-safe-smql-results"
}
```

### Transport-Token

Die Engine erzeugt beim Start `html/keys/local_transport.token`. PHP und die externen Tools lesen diese Datei und senden den Header:

```text
X-Mycelia-Local-Token
```

Dadurch ist die lokale Engine-API zusätzlich gegen lokale Proxy-/MITM-Prozesse gehärtet.


---

## 18. Projektstand v1.21.25: Media-Attractor-System und Blog-Erstellungs-Medien

Die Dokumentation v1.20.1 bleibt für Strict-VRAM-Audit, Native-VRAM-Bridge, Heartbeat-Audit, SMQL, Föderation, Provenance, Local Transport Security und Quantum Guard gültig. Ergänzt wird der aktuelle Web-Fixstand v1.21.25, weil die Content-Oberfläche inzwischen Bilder, Videos und sichere Medienlinks nicht nur in Forum und Blogposts, sondern auch bei der Blog-Erstellung unterstützt.

### 18.1 Geänderte Datenhaltung

Medien werden als eigene Attraktoren gespeichert:

```text
mycelia_media_nodes
```

Wichtige Felder:

| Feld | Bedeutung |
|---|---|
| `target_signature` | Signatur des Zielobjekts |
| `target_type` | `forum_thread`, `comment`, `blog` oder `blog_post` |
| `media_kind` | Upload oder Embed |
| `mime` | MIME-Typ des Uploads |
| `data_uri` | renderbare Bilddaten für kleine Webuploads |
| `embed_url` | geprüfter Medienlink |
| `title` | optionale Beschreibung |
| `moderation_status` | Sichtbarkeitsstatus |
| `deleted` | Soft-Delete-Marker |

### 18.2 Geänderte Direct-Ingest-Normalisierung

Der Direct-Ingest-Normalizer erhält Media-Felder jetzt explizit. Ohne diese Konservierung wurden Datei- und Linkfelder nach dem WebCrypto-Submit verworfen, obwohl sie im Browser korrekt gelesen wurden.

Konservierte Felder:

```text
media_file_b64
media_file_name
media_mime
media_size_bytes
file_b64
file_name
mime
embed_url
media_embed_url
media_title
title_media
```

Betroffene Operationen:

```text
create_forum_thread
update_forum_thread
create_blog
update_blog
create_blog_post
update_blog_post
```

### 18.3 Sichtbarkeit in PHP-Seiten

Aktualisierte Seiten:

| Datei | Änderung |
|---|---|
| `www/forum.php` | rendert Thread-Medienvorschauen |
| `www/thread.php` | rendert Thread-Mediengalerie |
| `www/blogs.php` | rendert Blog-Medienvorschauen |
| `www/blog.php` | rendert Blog- und Blogpost-Medien |
| `www/my_blog.php` | erlaubt Medien bei Blog-Erstellung/Bearbeitung und zeigt Medien an |
| `www/assets/direct-ingest.js` | liest Uploads und versiegelt Media-Felder |

### 18.4 Bedienung

Für Forum, Blog und Blogposts gilt:

1. Formular öffnen.
2. Optional Bild auswählen oder sicheren Medienlink eintragen.
3. Optional Medientitel/Beschreibung ergänzen.
4. Speichern.
5. Nach erfolgreichem Redirect muss die Galerie oder Vorschau sichtbar sein.

Unterstützte Uploads:

```text
JPEG
PNG
GIF
WebP
max. 3 MB
```

Unterstützte sichere Links:

```text
YouTube
Vimeo
HTTPS-Bilder
```

### 18.5 Diagnose bei fehlender Anzeige

Wenn keine Bilder/Videos erscheinen, ist der wichtigste Engine-Log-Indikator:

```text
query_sql_like: Tabelle=mycelia_media_nodes ... Treffer=0
```

Das bedeutet: Es wurde kein Media-Node gespeichert. In diesem Fall prüfen:

1. Aktuellen v1.21.25-Stand einspielen.
2. Python-Engine neu starten.
3. PHP-Server neu starten.
4. Browser mit `Strg + F5` hart neu laden.
5. Medium erneut anhängen, weil alte fehlgeschlagene Uploadversuche keinen Media-Node erzeugt haben.

Wenn `Treffer>0` erscheint, aber nichts sichtbar ist, liegt das Problem eher im Rendering oder in einer Content-Security-/Browser-Anzeigegrenze.

### 18.6 Sicherheitsabgrenzung

Media-Anzeige gehört zum normalen Web-UI-Pfad. Sie materialisiert autorisierte Inhalte für HTML und Browser. Daraus darf kein Strict-VRAM-Evidence-Status abgeleitet werden. Der Strict-VRAM-Audit bleibt an den separaten Random-Secret-Probe ohne geöffnete Weboberfläche gebunden.

### 18.7 Teststand

```text
Ran 8 tests in 2.146s
OK
```


---

## 18. Aktualisierung v1.21.25: E2EE-Mailbox, Profil-Nachrichten und aktuelle Prüfpunkte

### 18.1 Neue Kommunikationskomponenten

Ab v1.21.25 gibt es ein vollständiges Nachrichtenmodell für Nutzer:

| Komponente | Zweck |
|---|---|
| `e2ee_recipient_directory` | Liefert E2EE-fähige Empfänger mit Nutzername, User-Signatur und aktuellem Public Key. |
| `e2ee_send_message` | Speichert browserseitig verschlüsselte Nachrichten als blinde Ciphertext-Attraktoren. |
| `e2ee_inbox` | Liefert empfangene Ciphertexts für den eingeloggten Nutzer. |
| `e2ee_outbox` | Liefert gesendete Ciphertexts für den eingeloggten Nutzer. |
| `e2ee_delete_message` | Löscht eine Nachricht mailbox-seitig. |
| `www/profile.php#messages` | Sichtbares Nachrichtenmenü mit Schreiben, Inbox, Outbox, Lesen, Antworten und Löschen. |
| `www/messages.php` | Kompatibilitätsroute auf das Profil-Nachrichtenmenü. |

### 18.2 Sicherheitsmodell der Nachrichten

Die Nachrichtentexte werden im Browser verschlüsselt. PHP und Engine erhalten bei produktivem Senden nur verschlüsselte Felder wie Ciphertext, Nonce und Schlüsselreferenzen. Die Engine bleibt für den Nachrichteninhalt blind und übernimmt nur:

- Zustellung,
- Rechteprüfung,
- Signatur-/Owner-Auflösung,
- Inbox-/Outbox-Persistenz,
- Löschmarkierung,
- Snapshot-Sicherung des Ciphertexts.

Die Nutzer sehen Klartext nur lokal im Browser beim Lesen der Nachricht. Dafür muss der lokale private Schlüssel verfügbar sein. Ohne passenden privaten Schlüssel bleibt der gespeicherte Nachrichteninhalt ein nicht nutzbarer Ciphertext.

### 18.3 Inbox und Outbox

Das Profil zeigt zwei getrennte Sichten:

| Sicht | Inhalt | Aktionen |
|---|---|---|
| Inbox | Empfangene Nachrichten | Lesen, Antworten, Löschen |
| Outbox | Gesendete Nachrichten | Lesen, Löschen |
| Schreibmaske | Neue Nachricht | Empfänger auswählen, verschlüsseln, senden |

Outbox-Lesbarkeit wird durch eine zusätzliche senderseitige verschlüsselte Kopie erreicht. Dadurch kann der Sender seine gesendeten Nachrichten lesen, ohne dass die Empfängerverschlüsselung aufgebrochen werden muss.

### 18.4 Empfänger-Verzeichnis

Das bisherige manuelle Kopieren von Signaturen und Public-Key-JWKs entfällt. Das Empfänger-Verzeichnis löst Nutzer auf E2EE-fähige Public Keys auf. Falls ältere Formulare noch eine Key-Signatur senden, kann die Engine den Besitzer ermitteln und auf die Nutzeridentität normalisieren.

### 18.5 Löschsemantik

Das Löschen ist mailbox-seitig. Ein Empfänger kann seine Inbox-Kopie löschen; ein Sender kann seine Outbox-Kopie löschen. Die Gegenstelle verliert dadurch nicht automatisch ihre eigene Mailbox-Ansicht. Diese Trennung vermeidet überraschende Zustandsänderungen und ist für Audit und Nutzererwartung robuster.

### 18.6 Direct-Ingest und E2EE

Die E2EE-Formulare nutzen weiterhin das Direct-Ingest-Gateway. Wichtig ist die Reihenfolge im Browser:

1. E2EE-JavaScript erzeugt Ciphertext und Nonce.
2. Direct-Ingest versiegelt das Formular.
3. PHP leitet den Envelope weiter.
4. Die Engine speichert nur die verschlüsselten Nachrichtendaten.

v1.21.25 hat dafür die Script-Reihenfolge und Header-Ausgabe korrigiert, damit keine Ausgabe vor `header()` erfolgt und `strict_types` direkt am Dateianfang bleibt.

### 18.7 Snapshot-Restore-Korrektur

v1.21.25 korrigiert das Verhalten bei fehlenden Snapshot-Dateien. Ein leerer Restore-Aufruf liefert jetzt einen Fehler, wenn der konfigurierte Snapshot fehlt. Nur explizite Legacy-Pfade nutzen den Autosave-Fallback.

### 18.8 Aktuelle Testlage

Der aktuelle Projektstand enthält Tests für:

- Direct-Ingest Replay-Schutz,
- Session-/Tokenbindung,
- E2EE-Empfängerauflösung,
- Media-Attractor-System,
- Snapshot-Fallback,
- Profil-/Mailbox-Funktionen,
- Plugin- und Datenschutzpfade,
- Native-VRAM-Reports und konservative Auditlogik.

Übersprungene Tests sind optionale Umgebungstests, etwa native Compile-Smoke-Tests, wenn der Testkontext keinen Compiler erkennt, oder Clean-Source-Tests ohne gebündelte Core-OpenCL-DLL.

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


## Implementierungsnotiz: Markdown-Vault statt serverseitigem Markdown-HTML

Die frühere serverseitige Markdown-HTML-Ausgabe wurde durch das Client-Markdown-Vault-Modell abgelöst. Der Server transportiert und speichert Vault-Capsules; das sichtbare Markdown-HTML entsteht im Browser.

Praktische Konsequenzen:

- Codeblöcke und Kopierbuttons entstehen clientseitig.
- PHP verarbeitet keine Markdown-Syntax in Klartext.
- PHP-Templates enthalten Platzhalter und Metadaten, aber keine Forum-/Blog-Klartextkörper.
- Lange Inhalte werden als Vault-Inhalt transportiert und nicht als PHP-gerenderte Textblöcke.
