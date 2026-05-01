# Whitepaper: MyceliaDB als autarke kognitive Datenbankplattform

**Version:** 1.21.21
**Datum:** 2026-04-30  
**Status:** Technisches Whitepaper auf Basis Projektstand v1.21.21: Enterprise-Sicherheit, Media-Attractor-System, Direct-Ingest Phase 2, E2EE-Recipient-Directory und Profil-integrierte Inbox/Outbox, öffentliche Blog-Kataloge, Enterprise-/Fun-Plugins und striktes Plugin-Aktivierungsmodell
**Projektkontext:** Verschmelzung eines PHP-Web-Frontends mit einer Python/OpenCL-basierten Core-Engine zu einer SQL-freien MyceliaDB-Plattform


> Hinweis zu Sicherheitsformulierungen: Diese Dokumentation beschreibt die implementierten Schutzmechanismen und prüfbaren Evidenzpfade. Es wird keine prozentuale Sicherheitsfestlegung verwendet. Entscheidend sind die konkret umgesetzten Mechanismen: Zero-Logic-Gateway, Direct-Ingest, Native-VRAM-Pfade, Session-/Tokenbindung, Log-Redaction, Snapshot-Verschlüsselung, E2EE-Mailbox und prüfbare Auditberichte.

---

## Executive Summary

MyceliaDB demonstriert in den vorliegenden Testdaten einen funktionsfähigen vertikalen Prototypen einer SQL-freien Web-Datenbankumgebung. Das PHP-Frontend läuft erfolgreich über den PHP-Development-Server auf `127.0.0.1:8090`, kommuniziert mit der lokalen Python-Engine `mycelia_platform.py` auf `127.0.0.1:9999`, registriert einen Nutzer als `mycelia_users`-Nutrient-Node und authentifiziert denselben Nutzer anschließend über ein gespeichertes Authentifizierungsmuster.

Die Logs zeigen außerdem, dass eine OpenCL-Initialisierung auf einer AMD-GPU (`gfx90c`) erfolgt, Kernel erfolgreich kompiliert werden und mindestens ein Simulationskernel (`subqg_simulation_step`) mit sehr geringer Laufzeit ausgeführt wird. Damit ist plausibel belegt, dass GPU-gestützte Rechenpfade im System vorhanden und aktiv sind.

Nicht belegt ist jedoch die starke Aussage, dass alle Daten ausschließlich im verschlüsselten GPU-Speicher existieren, dass das System im sicherheitstechnischen Sinne „unhackbar“ sei oder dass eine pauschale Sicherheitsstufe bewiesen wurde. Die Logs stützen einen erfolgreichen Proof of Concept, aber keinen kryptografischen Sicherheitsbeweis und keine vollständige Persistenzanalyse. Das System ist daher professionell als experimentelle, GPU-gestützte, SQL-freie kognitive Datenbankplattform einzuordnen, nicht als nachgewiesen unhackbare Produktionsdatenbank.

---

## 1. Ausgangslage und Zielsetzung

Klassische Webanwendungen trennen typischerweise:

- Frontend-Logik in PHP, JavaScript oder einem Webframework,
- Datenhaltung in einer relationalen SQL-Datenbank,
- Authentifizierung über eine `users`-Tabelle,
- Persistenz über SQL-Abfragen, Indizes und Transaktionen.

MyceliaDB ersetzt diese Architektur durch ein anderes Modell:

1. SQL-Dumps werden nicht in MySQL importiert.
2. Datensätze werden in eine `DynamicAssociativeDatabase` überführt.
3. Jeder Datensatz wird als sogenannter Nutrient-Node im Myzel-Netzwerk repräsentiert.
4. Authentifizierung erfolgt nicht über eine klassische SQL-`users`-Tabelle, sondern über Musterabgleich im `CognitiveCore`.
5. PHP dient als Web-Gateway, während Python/OpenCL die Engine-Schicht bildet.
6. GPU-Kernel übernehmen rechenintensive Simulations-, Diffusions-, neuronale oder kryptografienahe Operationen.

Das Ziel ist eine Datenbankumgebung, die SQL-Dumps „frisst“, daraus ein assoziatives Netzwerk erzeugt und den Zugriff ausschließlich über die Mycelia-Schicht erlaubt.

---

## 2. Prüfgrundlage

Dieses Whitepaper basiert auf folgenden vorliegenden Artefakten:

### 2.1 Web-Frontend

Der Screenshot des Startbildschirms zeigt drei zentrale Funktionen:

- Login via Attraktor
- Registrierung als Nutrient-Node
- SQL-Dump-Import

Der Screenshot des Profilbereichs zeigt einen erfolgreich rekonstruierten Nutzerknoten:

- Nutzername bzw. Begrüßung: `Ralf`
- Tabelle: `mycelia_users`
- Signatur: `1e895cbf27d0...`
- Stabilität: `0.985`
- Storage-Hinweis: `encrypted-attractor / no SQL`

### 2.2 PHP-Server-Log

Der PHP-Development-Server konnte auf Port `8080` nicht starten, wurde aber erfolgreich auf Port `8090` gestartet:

```text
PHP 8.4.20 Development Server (http://127.0.0.1:8090) started
```

Anschließend wurden erfolgreiche HTTP-Requests sichtbar:

```text
GET /index.php      -> 200
POST /index.php     -> 200
POST /index.php     -> 302
GET /profile.php    -> 200
```

Das belegt, dass das Web-Frontend bedienbar ist und ein Login-Vorgang bis zur Profilseite durchgeführt wurde.

### 2.3 Python/OpenCL-Engine-Log

Die Engine meldet:

```text
MyceliaDB Platform listening on 127.0.0.1:9999 (offline+gpu-crypto)
```

Die OpenCL-Initialisierung meldet:

```text
Using platform: AMD Accelerated Parallel Processing
Found 2 GPU devices
Using device index 0: gfx90c
FP64 Support: Yes
64-bit atomics SUPPORTED
All kernels compiled successfully
Initialization OK for GPU 0 (gfx90c)
```

Außerdem werden Kernel kompiliert, darunter:

- `fused_diffusion`
- `izhikevich_neuron_step`
- `stdp_update_step`
- `subqg_simulation_step`
- `brain_bridge_cycle`
- `quantum_apply_single_qubit`

Die Registrierung und spätere Authentifizierung erscheinen in den Logs als:

```text
CognitiveCore.query_sql_like: Tabelle=mycelia_users Filter={'username': 'Ralf'} Treffer=0
DynamicAssociativeDatabase.store_sql_record: Tabelle=mycelia_users Signature=1e895cbf27d0 Stabilität=0.985
CognitiveCore.query_sql_like: Tabelle=mycelia_users Filter={'username': 'Ralf', 'auth_pattern': '7701eb...'} Treffer=1
```

---

## 3. Prüfung der Aussage „State of the Art für eine autarke Datenbank“

Die Aussage ist teilweise zutreffend, muss aber technisch präzisiert werden.

### 3.1 Zutreffend

Die Logs zeigen einen funktionsfähigen lokalen Prototypen mit folgenden Eigenschaften:

- Das Web-Frontend verwendet keine sichtbare MySQL-Interaktion im Testablauf.
- Die Python-Engine nimmt Requests entgegen.
- Ein Nutzer wird als Eintrag in `mycelia_users` über die Mycelia-Schicht gespeichert.
- Der Login erfolgt über einen `auth_pattern`-Filter gegen den `CognitiveCore`.
- OpenCL-Kernel werden auf einer AMD-GPU kompiliert.
- Simulationskernel werden zur Laufzeit ausgeführt.

Damit ist die Aussage gerechtfertigt, dass ein autarker, SQL-freier Datenpfad für Registrierung, Login und Profilrekonstruktion demonstriert wurde.

### 3.2 Nicht ausreichend belegt

Folgende Aussagen sind durch die Logs nicht bewiesen:

| Aussage | Bewertung | Begründung |
|---|---:|---|
| „Alle Informationen existieren ausschließlich im verschlüsselten GPU-Speicherraum“ | Nicht belegt | Die Logs zeigen GPU-Initialisierung und `offline+gpu-crypto`, aber keine vollständige Speicherresidenzprüfung. Es ist unklar, welche Daten im RAM, in Dateien, in Python-Objekten oder im GPU-Speicher liegen. |
| Absolute Unangreifbarkeit | Fachlich nicht behauptet | Die implementierte Sicherheit reduziert die klassischen Web-/SQL-Angriffswege stark, weil PHP im Normalbetrieb keine Formular- oder Content-Klartexte erhält. Realistische Prüfbereiche bleiben Gateway-Konfiguration, lokale Engine-API, Session-/Token-Bindung, Native-/Python-Grenzen, Dateirechte, Log-Redaction, kontrollierte Memory-Probes und Supply Chain. Diese Bereiche sind im Code nicht ungeschützt, sondern durch Allowlists, Opaque-Transport, Redaction, Tokenbindung, Native-Authentizität und Evidence-Prüfungen begrenzt. |
| „Pauschale Prozent-Sicherheitsstufe bewiesen“ | Nicht belegt | Es gibt keinen formalen Sicherheitswert, keine definierte Messgröße und keine reproduzierbare Sicherheitsstudie in den Logs. |
| „Hacker müssten die Simulation in Echtzeit mitgehen“ | Spekulativ | Alternative Angriffspfade müssen gegen die bereits implementierten Kontrollen getestet werden: Zero-Logic-Gateway, sealed Direct Ingest, Engine-Session-Bindung, Tokenrotation, Localhost-Transportregeln, Log-Redaction, Native-Library-Authentizität und kontrollierte Memory-Probes. Ein erfolgreicher Fehlpfad soll nach aktuellem Modell keine unmittelbar nutzbaren Nutzdaten liefern, sondern höchstens abgelehnte Requests, opaque Handles, Signaturen, redigierte Metadaten oder verschlüsselte Pakete. |
| „Statischer Festplattenangriff findet nur Rauschen“ | Nicht belegt | Dafür müsste nachgewiesen werden, dass keine Klartextdaten, Hashes, Sessions, Dumps, Logs oder Cache-Dateien auf der Platte liegen. |

### 3.3 Professionelle Einordnung

Korrekt wäre folgende technische Formulierung:

> Die vorliegenden Logs belegen einen funktionierenden Proof of Concept einer SQL-freien, lokal autarken MyceliaDB-Plattform mit PHP-Frontend, Python-Engine, DAD-basierter Datensatzrepräsentation, CognitiveCore-basierter Authentifizierung und aktivierter OpenCL-GPU-Schicht. Die Sicherheits- und Persistenzeigenschaften sind vielversprechend, aber noch nicht formal bewiesen.

---

## 4. Architekturübersicht

### 4.1 Schichtenmodell

```text
┌────────────────────────────────────────────┐
│ PHP Web-Frontend                            │
│ index.php, profile.php, api.php             │
│ Login, Registrierung, Profil, Dump-Import   │
└───────────────────────┬────────────────────┘
                        │ HTTP/JSON localhost
                        ▼
┌────────────────────────────────────────────┐
│ Mycelia Platform Bridge                     │
│ mycelia_platform.py                         │
│ register_user, login_attractor, import_dump │
│ query_pattern, check_integrity              │
└───────────────────────┬────────────────────┘
                        │ Engine API
                        ▼
┌────────────────────────────────────────────┐
│ CognitiveCore + DynamicAssociativeDatabase │
│ Attraktorbildung, Pattern-Abgleich, DAD     │
│ Nutrient-Nodes aus SQL-Datensätzen          │
└───────────────────────┬────────────────────┘
                        │ Rechenpfad
                        ▼
┌────────────────────────────────────────────┐
│ OpenCLDriver / OfflineDriver Hybrid         │
│ GPU-Kernel, Simulation, Crypto-nahe Pfade   │
│ AMD Accelerated Parallel Processing gfx90c  │
└────────────────────────────────────────────┘
```

### 4.2 Kontrollfluss bei Registrierung

1. Nutzer trägt Daten in das Registrierungsformular ein.
2. PHP sendet die Daten an `mycelia_platform.py`.
3. Die Engine prüft über `CognitiveCore.query_sql_like`, ob ein Knoten mit demselben Username existiert.
4. Bei `Treffer=0` wird ein neuer Datensatz in `DynamicAssociativeDatabase.store_sql_record` geschrieben.
5. Der Datensatz erhält eine Signatur und einen Stabilitätswert.
6. Der Nutzer ist nicht Teil einer SQL-Tabelle, sondern ein Mycelia-Nutrient-Node in der DAD-Schicht.

Log-Beleg:

```text
CognitiveCore.query_sql_like: Tabelle=mycelia_users Filter={'username': 'Ralf'} Treffer=0
DynamicAssociativeDatabase.store_sql_record: Tabelle=mycelia_users Signature=1e895cbf27d0 Stabilität=0.985
```

### 4.3 Kontrollfluss bei Login

1. Nutzer sendet Username und Passwort.
2. Das Passwort wird in ein Authentifizierungsmuster überführt.
3. Die Engine sucht nach einem passenden Muster:

```text
Filter={'username': 'Ralf', 'auth_pattern': '7701eb...'}
```

4. Bei `Treffer=1` wird Zugriff gewährt.
5. PHP leitet auf `profile.php` weiter.
6. Das Profil rekonstruiert die gespeicherten Attribute aus dem Mycelia-Knoten.

Log-Beleg:

```text
CognitiveCore.query_sql_like: Tabelle=mycelia_users Filter={'username': 'Ralf', 'auth_pattern': '7701eb...'} Treffer=1
```

---

## 5. SQL-Dump-zu-Mycelia-Übergang

Die zentrale Designentscheidung besteht darin, SQL-Dumps nicht mehr in eine relationale Engine zurückzuführen. Stattdessen werden sie als Rohmaterial betrachtet.

### 5.1 Alter Ansatz

```text
.sql Dump -> MySQL Import -> Tabellen -> SELECT/INSERT/UPDATE
```

### 5.2 Neuer Ansatz

```text
.sql Dump -> sql_importer.py -> Datensatzparser -> Nutrient-Node -> DynamicAssociativeDatabase
```

### 5.3 Bedeutung

Der SQL-Dump ist nur noch ein Futterformat. Nach dem Import wird die relationale Struktur nicht als laufende Datenbankinstanz benötigt. Tabellenname, Spaltenwerte und Datensatzinhalt werden in eine assoziative Signatur überführt.

Ein Datensatz wird damit nicht primär als Zeile verstanden, sondern als Muster mit folgenden Eigenschaften:

- semantischer Herkunft: Tabellenname
- struktureller Herkunft: Spaltennamen
- Nutzlast: Feldwerte
- Signatur: Identifikator des Attraktors
- Stabilität: Bewertung der internen Musterkonsistenz
- Rekonstruktionspfad: Abfrage über CognitiveCore/QuantumOracle-artige Mechanismen

---

## 6. GPU- und OpenCL-Schicht

### 6.1 Was die Logs tatsächlich zeigen

Die Engine findet eine AMD OpenCL-Plattform, erkennt zwei GPU-Geräte und nutzt `gfx90c`. Sie meldet Unterstützung für FP64 und 64-Bit-Atomics. Außerdem werden zahlreiche Kernel kompiliert.

Das ist ein wichtiger technischer Meilenstein, weil dadurch ein möglicher Pfad entsteht, Datenbankoperationen nicht mehr ausschließlich über Python-Objektlisten, Dictionaries oder SQL-Indizes laufen zu lassen, sondern über vektorisierte, parallele Rechenstrukturen.

### 6.2 Bedeutung der Kernel

| Kernel-Familie | Mögliche Rolle in MyceliaDB |
|---|---|
| `fused_diffusion` | Ausbreitung von Aktivierung oder Ähnlichkeit über das Netzwerk |
| `izhikevich_neuron_step` | neuronale Zustandsdynamik für kognitive Simulationen |
| `stdp_update_step` | plastische Gewichtsanpassung, potenziell für selbstorganisierende Indexstrukturen |
| `subqg_simulation_step` | Simulationsschritt für Attraktor- oder Rauschdynamik |
| `quantum_apply_single_qubit` | experimentelle Quanten-/Zustandsoperationen |
| `matrix_multiply`, `softmax`, `layer_norm` | klassische Beschleuniger für neuronale oder embeddingbasierte Operationen |

### 6.3 Vorsicht bei der Interpretation

Dass Kernel kompiliert werden, bedeutet nicht automatisch, dass alle Datenbankoperationen vollständig auf der GPU ausgeführt werden. Dafür müssten zusätzlich nachgewiesen werden:

- Welche Datenstrukturen tatsächlich in GPU-Buffern liegen.
- Ob CPU-Klartextkopien nach Nutzung gelöscht werden.
- Ob DAD-Knoten persistiert werden und wo.
- Ob Logs sensible Daten enthalten.
- Ob Dumps nach Import gelöscht oder verschlüsselt werden.
- Ob Sessions Klartextdaten speichern.
- Ob PHP außerhalb des autorisierten DSGVO-Exports jemals Profil- oder Content-Felder im Klartext hält; im implementierten Direct-Ingest-/Zero-Logic-Gateway-Modell soll dies nicht passieren.

---



## Korrektur v1.21.21: PHP-blinder Sicherheitsrand

Die Sicherheitsbeschreibung wurde präzisiert: PHP ist im implementierten Normalbetrieb **keine Klartext-Verarbeitungsschicht** für Formular-, Forum-, Blog-, Medien- oder Admin-Mutationen. Produktive Mutationen laufen über Direct Ingest: Der Browser versiegelt die Nutzdaten, PHP erhält `sealed_ingest` und `direct_op`, und das Zero-Logic-Gateway blockiert Klartext-POSTs.

Die Ausnahme ist bewusst und fachlich notwendig: **DSGVO / Eigene Daten herunterladen**. Dieser Pfad erzeugt autorisierten Klartext, weil der Nutzer seine eigenen Daten exportieren können muss. Diese Ausnahme ist kein Widerspruch zum PHP-blinden Mutationsmodell, sondern ein expliziter Exportpfad.

Deshalb ist die Angriffsfläche nicht pauschal „PHP sieht Klartext“, sondern präziser:

| Bereich | Implementierte Sicherheitswirkung | Verbleibender Prüfpunkt |
|---|---|---|
| PHP-POST | Klartext-POSTs für produktive Mutationen werden blockiert | Gateway-Allowlist, Fallback-Routen, Fehlerseiten |
| PHP-Session | PHP hält opaques Engine-Session-/Tokenmaterial | Tokenrotation, CSRF-/Replay-Schutz, Session-Fixation |
| Medien-Upload | Dateien werden über Direct-Ingest-Felder transportiert | Größenlimits, MIME-Prüfung, Moderationsstatus, Data-URI-Ausgabe |
| Lokale Engine-API | Mutationen werden durch Engine-Session und Token geprüft | Localhost-Zugriff, Command-Allowlist, Firewall/Host-Isolation |
| Engine/Native | Rekonstruktion und Residency werden durch Evidence geprüft | Memory-Probes, Native-Bibliotheksauthentizität, Logs |
| DSGVO-Export | Bewusste Klartextausgabe an den berechtigten Nutzer | Zugriffskontrolle, Rate-Limits, Audit-Logging |

## 7. Sicherheitseinordnung

### 7.1 Hardware-Residency als kritischer Sicherheitsanker

Ein zentraler Punkt für die postulierte „Strict-VRAM-Sicherheit“ ist nicht nur, dass OpenCL-Kernel kompiliert und Simulationsschritte auf der GPU ausgeführt werden. Entscheidend ist der Nachweis der **Hardware-Residency**: Entschlüsselung, Rekonstruktion und Musterabgleich müssen in-flight innerhalb des VRAMs stattfinden, ohne dass Klartextprofile, SQL-Ursprungszeilen oder rekonstruierte Dokumente jemals im CPU-RAM materialisiert werden.

Wäre dieser Nachweis belastbar, entstünde ein starkes Alleinstellungsmerkmal gegenüber klassischen TEE-Lösungen. Trusted Execution Environments schützen üblicherweise CPU-seitige Enklaven und reduzieren die Angriffsfläche gegenüber normalen Prozessen. MyceliaDB würde dagegen eine andere Schutzklasse anstreben: Daten bleiben als verschlüsselte Attraktorfragmente bzw. Rekonstruktionszustände im GPU-Speicherraum und werden nur als minimale, kontrollierte Antwortform an das Frontend zurückgegeben. Der Sicherheitsgewinn wäre nicht nur kryptografisch, sondern architektonisch: Angriffe auf SQL-Dumps, Datenbankdateien, ORM-Objekte, klassische Query-Caches und CPU-seitige Tabellenstrukturen verlieren ihr primäres Ziel.

Der aktuelle Testlog beweist diesen Zustand noch nicht vollständig. Er zeigt OpenCL-Aktivität, erfolgreiche Kernelkompilierung und GPU-nahe Kryptopfade, aber kein negatives Speicherforensik-Ergebnis für CPU-RAM. Deshalb wurde im Projekt ein konservativer, maschinenlesbarer `residency_report` ergänzt. Dieser Report unterscheidet zwischen:

- SQL-freiem Betrieb,
- aktiver OpenCL-Schicht,
- aktivem GPU-Kryptopfad,
- strengem In-flight-VRAM-Anspruch,
- verbleibendem CPU-Klartext-Risiko.

Damit wird die Sicherheitsbehauptung testbar statt rhetorisch. Der nächste Reifegrad ist erst erreicht, wenn automatisierte Tests mit Speicherproben, Prozessdumps und Hooking nachweisen, dass sensible Klartextfragmente während Authentifizierung, Snapshot-Restore und Query-Rekonstruktion nicht im CPU-RAM erscheinen.


### 7.1 Reale Sicherheitsgewinne

MyceliaDB kann gegenüber klassischen PHP/MySQL-Anwendungen folgende strukturelle Vorteile haben:

| Sicherheitsaspekt | Klassische PHP/MySQL-App | MyceliaDB-Prototyp |
|---|---|---|
| SQL-Injection | Zentrale Gefahr bei unsauberer Query-Erzeugung | Reduziert, weil keine SQL-Engine im Request-Pfad |
| Tabellendump aus MySQL | Typischer Angriffspfad | Nicht vorhanden, sofern keine SQL-DB existiert |
| Datenmodell | Explizite Tabellen und Spalten | Attraktor-/Signaturmodell erschwert direkte Interpretation |
| Rechenpfad | CPU/SQL-Engine | Python/OpenCL-Hybrid |
| Authentifizierung | Tabellenbasierter Credential-Vergleich | Pattern-Abgleich über CognitiveCore |

### 7.2 Abgesicherte Prüfzonen statt pauschaler Angriffsflächen

Die folgenden Bereiche sind keine pauschal offenen Klartext-Lecks. Sie sind im aktuellen Code soweit wie möglich abgesichert und werden deshalb als Prüfzonen beschrieben:

1. **PHP-Gateway:** Produktive Mutationen laufen über `sealed_ingest` und `direct_op`. PHP bekommt im Normalbetrieb keine Formular-, Forum-, Blog-, Medien- oder Admin-Klartexte, sondern nur versiegelte Pakete und opaque Session-Informationen. Die bewusste Ausnahme bleibt der DSGVO-Export „Eigene Daten herunterladen“.
2. **Dump-Import:** SQL-Dumps sind untrusted input, werden aber nicht als laufende SQL-Datenbank eingebunden. Entscheidend sind Parser-Fuzzing, Pfad-Whitelisting, Größenlimits und die Prüfung, dass importierte Inhalte als Mycelia-Attraktoren weiterverarbeitet werden.
3. **Localhost-API:** Die Engine-API ist lokal gebunden und wird über erlaubte Commands, Engine-Sessions, Tokenbindung und kontrollierte Web-Gateways genutzt. Ein Fehlzugriff soll keine verwertbaren Nutzdaten, sondern abgelehnte Requests oder nicht interpretierbare Handles erzeugen.
4. **Session-/Tokenmodell:** PHP hält keine autoritative Fachlogik, sondern ein opaques Engine-Session-Handle und rotierende Request-Tokens. Rollen, Owner und Zielsignaturen werden Engine-seitig geprüft und injiziert.
5. **Logs:** Produktiv relevante Logs müssen redigiert sein. Signaturen und operative Handles sind nicht automatisch Klartextdaten; vollständige Auth-Pattern, personenbezogene Werte und Exportinhalte dürfen nicht unredigiert protokolliert werden.
6. **Speicher und Rekonstruktion:** PHP-POST-Variablen und PHP-HTTP-Bodies enthalten im Normalbetrieb keine Formular-Klartexte. Speicherprüfungen zielen auf Engine-/Native-Grenzen, DSGVO-Exportpfade und autorisierte Rekonstruktionspunkte. Ein möglicher Treffer muss klassifiziert werden: sensibler Klartext, public identifier, redigierte Metadaten oder nicht nutzbares Cipher-/Envelope-Material.
7. **GPU-/Native-Pfad:** GPU-Residency wird nicht rhetorisch behauptet, sondern über Selftests, Capability-Reports, Native-Library-Authentizität und externe Memory-Probes gestützt. Debug-/Treiberpfade bleiben Audit-Thema, nicht pauschaler Datenabfluss.
8. **Fallback-/Hybridmodus:** Hybridzustände müssen maschinenlesbar ausgewiesen werden, damit Leser erkennen, ob ein Pfad `offline`, `opencl`, `native-vram` oder auditfähig läuft.

### 7.3 Bewertung der „Unhackbarkeit“

Die Bezeichnung „unhackbar“ sollte nicht verwendet werden. Professionell belastbar ist:

> MyceliaDB reduziert bestimmte klassische Angriffsklassen relationaler Webanwendungen, insbesondere SQL-Injection und direkte Datenbankdump-Angriffe, sofern tatsächlich keine SQL-Engine und keine Klartextpersistenz im Betrieb vorhanden sind. Eine belastbare Sicherheitsbewertung beschreibt deshalb nicht pauschal offene Schwachstellen, sondern prüft, ob die implementierten Kontrollen in Grenzfällen weiterhin nur nicht nutzbare, opaque, redigierte oder verschlüsselte Artefakte preisgeben.

---

## 8. Technischer Durchbruch: Was wirklich erreicht wurde

Der echte Fortschritt liegt nicht in einer absoluten Sicherheitsbehauptung, sondern in der Architekturverschiebung.

### 8.1 Von Tabellen zu Attraktoren

Klassische Datenbanken speichern Datensätze als Zeilen. MyceliaDB speichert oder modelliert sie als Attraktoren. Dadurch wird ein Datensatz nicht nur durch Primärschlüssel adressiert, sondern durch ein Muster, das stabil genug sein muss, um später wiedergefunden oder rekonstruiert zu werden.

Das erlaubt neue Abfragetypen:

- exakte Suche: Username entspricht Muster
- unscharfe Suche: ähnliche Signaturen
- assoziative Suche: verwandte Knoten
- Integritätsprüfung: Stabilitätswerte und Signaturkonsistenz
- importierte Relationen: Tabellenbezüge als Netzwerkstruktur

### 8.2 Von SQL-Abfrage zu kognitivem Pattern Matching

`CognitiveCore.query_sql_like` ist noch dem Namen nach SQL-ähnlich, aber der relevante Punkt ist: Die Abfrage wird als Filtermuster formuliert. Die Engine kann intern entscheiden, ob sie dieses Muster über Dictionary-Lookup, DAD-Signatur, Embedding, Simulation oder GPU-Ähnlichkeitssuche auflöst.

Das ist ein wichtiger Abstraktionswechsel:

```text
SELECT * FROM users WHERE username=? AND password_hash=?
```

wird zu:

```text
find stable attractor matching {
    table: mycelia_users,
    username: Ralf,
    auth_pattern: 7701eb...
}
```

### 8.3 Von Datenhaltung zu Rekonstruktion

Das UI spricht von „rekonstruierten Profildaten“. Das deutet auf ein Modell hin, bei dem Daten nicht zwingend als direkt sichtbare Zeile präsentiert werden, sondern über eine Rekonstruktionsfunktion aus der Mycelia-Schicht zurückgegeben werden.

Das kann nützlich sein, wenn später folgende Mechanismen ergänzt werden:

- verschlüsselte Payload-Segmente,
- GPU-residente Merkmalsvektoren,
- rekonstruktive Decoder,
- redundante Knotenfragmente,
- Integritätsprüfung über Signaturen,
- Rauschfelder als Schutz gegen triviale Speicheranalyse.

---

## 9. Architekturqualität und aktueller Reifegrad

### 9.1 Erreicht

| Fähigkeit | Status aus Logs |
|---|---|
| PHP-Frontend startet | Erreicht auf Port `8090` |
| Registrierung funktioniert | Erreicht |
| Login funktioniert | Erreicht |
| Profilseite wird angezeigt | Erreicht |
| Python-Engine lauscht lokal | Erreicht auf `127.0.0.1:9999` |
| DAD speichert Nutzerdatensatz | Erreicht |
| CognitiveCore findet Auth-Pattern | Erreicht |
| OpenCL-GPU wird initialisiert | Erreicht |
| Kernel werden kompiliert | Erreicht |
| SQL-freier Webpfad im Test | Plausibel erreicht |

### 9.2 Noch offen

| Fähigkeit | Status |
|---|---|
| Vollständige Entfernung aller SQL-Reste im gesamten Repository | Muss per Code-Audit geprüft werden |
| Garantiert keine Klartextpersistenz | Nicht belegt |
| Ausschließliche GPU-Datenhaltung | Nicht belegt |
| Produktdaten vollständig migriert | Muss mit Shop-Tests geprüft werden |
| SQL-Dump-Import großer Dumps | Noch Benchmark nötig |
| Authentifizierung resistent gegen Timing/Replay | Noch Sicherheitsprüfung nötig |
| Crash-Recovery ohne SQL | Noch Architekturprüfung nötig |
| Multi-User-Isolation | Noch zu testen |
| Transaktionsmodell | Nicht sichtbar |
| Backup/Restore-Modell | Nicht sichtbar |

---

## 10. Benchmark-Design

Um die Leistungs- und Sicherheitsbehauptungen überprüfbar zu machen, sollte MyceliaDB anhand reproduzierbarer Benchmarks gemessen werden.

### 10.1 Import-Benchmark

**Ziel:** Prüfen, wie schnell SQL-Dumps in Nutrient-Nodes überführt werden.

**Testdaten:**

- 1.000 Nutzer
- 100.000 Nutzer
- 1.000.000 Produktdatensätze
- gemischte Dumps mit Sonderzeichen, NULL-Werten, langen Textfeldern

**Metriken:**

- Datensätze pro Sekunde
- Peak-RAM
- GPU-Speicherbelegung
- Fehlerquote des Parsers
- Importzeit pro Tabellengröße
- Stabilitätsverteilung der erzeugten Nodes

**Hypothese:**

MyceliaDB importiert kleine und mittlere Dumps ohne MySQL-Instanz und erzeugt stabile Attraktoren mit reproduzierbaren Signaturen.

**Gegenhypothese:**

Parserkosten, Python-Objektkosten oder Rekonstruktionskosten dominieren, sodass MySQL beim reinen Import schneller und robuster bleibt.

### 10.2 Query-Benchmark

**Ziel:** Vergleich zwischen klassischer Suche und Mycelia-Pattern-Suche.

**Baseline:**

- SQLite oder MySQL mit Index auf `username`
- Python-Dictionary als Minimalbaseline
- Mycelia `query_pattern` / `query_sql_like`

**Metriken:**

- Latenz p50/p95/p99
- Trefferquote
- False Positives bei unscharfen Mustern
- CPU/GPU-Auslastung
- JSON-Overhead zwischen PHP und Python

**Hypothese:**

Bei assoziativen oder unscharfen Abfragen kann das Mycelia-Modell einen strukturellen Vorteil gegenüber SQL entwickeln.

**Gegenhypothese:**

Bei exakten Key-Value-Abfragen bleibt ein Dictionary oder SQL-Index schneller.

### 10.3 Sicherheitsbenchmark

**Ziel:** Validieren, dass keine klassischen Datenbankangriffe mehr greifen und keine neuen kritischen Lecks entstehen.

**Tests:**

- SQL-Injection-Payloads gegen alle Formulare
- Pfadmanipulation beim Dump-Import
- Replay-Angriffe gegen Login-Requests
- Session-Fixation
- Log-Leakage-Analyse
- Speicheranalyse nach Registrierung/Login
- Dump-Reste auf Festplatte
- Fuzzing des SQL-Importers

**Erfolgskriterien:**

- Keine SQL-Verbindung im Prozess.
- Keine Klartextpasswörter in Logs, Dateien oder Sessions.
- Auth-Pattern nicht direkt als wiederverwendbares Passwortäquivalent nutzbar.
- Importer akzeptiert nur erlaubte Pfade und Dateigrößen.
- Abfragen sind rate-limited und auditierbar.

---

## 11. Prüfzonen und Scheitermodi

### 11.1 Technische Prüfzonen

| Prüfzone | Möglicher Fehlzustand | Implementierte oder empfohlene Begrenzung |
|---|---|---|
| GPU-Treiber nicht verfügbar | Engine fällt in Fallback oder startet nicht | Explizite Capability-Matrix und Healthcheck |
| Hybridzustand `offline+gpu-crypto` unklar | Falsche Sicherheitsannahmen | Präzise Runtime-Modi: `offline`, `gpu`, `gpu_verified` |
| Logs ohne Redaction | Diagnoseausgaben könnten zu aussagekräftig werden | Redaction für Auth-Pattern, personenbezogene Daten und Exportinhalte; Signaturen als public identifier klassifizieren; Ziel: keine nutzbaren Nutzdaten |
| Dump-Importer ohne Pfadkontrolle | Import unerwünschter Dateien statt nutzbarer Datenextraktion | Whitelist-Verzeichnis, canonical path checks, Größenlimits, Fuzzing |
| Keine Transaktionen | Inkonsistente Knoten bei Crash | Write-ahead-Node-Journal oder atomare Snapshots |
| Unklare Persistenz | Leser könnten Snapshot-, Cache- und Restore-Pfade falsch bewerten | Persistenzmodell dokumentieren und testen; Ziel: verschlüsselte Snapshots statt lesbarer Datenbankartefakte |
| Session-/Token-Drift | Falsche Zuordnung oder Replay-Versuch | Engine-Session-Binding, One-Time-Token-Pool, Rotation, Owner-Prüfung in der Engine |
| Rekonstruktionsfehler | Falsche Profildaten | Signaturprüfung, Checksummen, Versionierung |

### 11.2 Offene Validierungsfragen

Das Attraktor-Modell ist ein Datenbankvorteil, wenn es reproduzierbar, messbar und kontrollierbar bleibt. Folgende Fragen sind Validierungsfragen, nicht Hinweise auf bekannte Datenlecks:

- Ist dieselbe Eingabe deterministisch derselbe Attraktor?
- Wie werden Kollisionen erkannt?
- Wie wird ein Datensatz gelöscht?
- Wie wird ein Feld aktualisiert?
- Wie wird Konsistenz über mehrere Knoten garantiert?
- Wie wird Backup und Restore durchgeführt?
- Wie wird verhindert, dass Rauschen Rekonstruktionen verfälscht?
- Welche Garantien gibt es bei Parallelzugriff?

---

## 12. Empfohlene nächste Entwicklungsschritte

### 12.1 Mycelia Snapshot Format als wichtigste Persistenzhürde

Ohne SQL-Persistenz muss MyceliaDB nach einem Kaltstart beweisen, dass der kognitive Zustand des Netzwerks aus einer binären, verschlüsselten Datei wiederhergestellt werden kann. Dieses Format darf keine lesbaren SQL-Tabellennamen, Profilfelder, Kundendaten oder ursprünglichen Dump-Strukturen enthalten. Der Snapshot ist damit kein Datenbankdump, sondern ein verschlüsseltes Attraktorabbild.

Die neue Implementierung führt dafür das Format `MYCELIA_SNAPSHOT_V1` ein. Es schreibt eine kleine binäre Magic-Signatur, eine Headerlänge und einen JSON-Header mit Metadaten, Seed, Ciphertext-Paket und Hash. Die eigentliche Datenbankstruktur liegt ausschließlich im verschlüsselten Paket. Ein Angreifer, der nur die Snapshot-Datei besitzt, soll daraus keine ursprünglichen SQL-Strukturen extrahieren können.

Der Kaltstartpfad lautet jetzt:

1. Web- oder API-Befehl `create_snapshot` erzeugt eine verschlüsselte Binärdatei.
2. Der Prozess kann beendet werden.
3. Ein neuer `MyceliaPlatform`-Prozess startet ohne SQL-Datenbank.
4. `restore_snapshot` entschlüsselt das Attraktorabbild und rekonstruiert die `DynamicAssociativeDatabase`.
5. Login über `login_attractor` funktioniert wieder gegen den rekonstruierten Auth-Attraktor.
6. Profil- und Produktdaten werden über den Quantum-/Crypto-Pfad rekonstruiert, nicht aus SQL gelesen.

Damit wird die bisherige „autarke“ Behauptung operationalisiert: MyceliaDB kann ihren Zustand ohne MySQL, ohne SQLite-Materialisierung und ohne SQL-Dump als laufende Persistenzquelle wiederherstellen.


### 12.1 Sofortmaßnahmen

1. **Log-Redaction einbauen**  
   Auth-Pattern, E-Mail-Adressen und personenbezogene Daten nicht vollständig loggen.

2. **Runtime-Modus sichtbar machen**  
   UI und API sollten anzeigen:

   ```json
   {
     "driver": "gpu",
     "gpu_verified": true,
     "device": "gfx90c",
     "sql_enabled": false,
     "cleartext_persistence": false
   }
   ```

3. **SQL-Restprüfung automatisieren**  
   Ein Test sollte das Repository nach `PDO`, `mysql`, `mysqli`, `new PDO`, `SELECT`, `INSERT INTO` in PHP-Persistenzpfaden durchsuchen.

4. **Importer absichern**  
   Nur Dumps aus einem festen `dumps/`-Verzeichnis akzeptieren. Keine absoluten Pfade aus Webformularen.

5. **Healthcheck erweitern**  
   `check_integrity` sollte nicht nur Engine-Erreichbarkeit melden, sondern auch:

   - GPU-Status,
   - Node-Anzahl,
   - Signaturkonsistenz,
   - Persistenzstatus,
   - SQL-Abwesenheit,
   - letzte Importfehler.

### 12.2 Mittelfristige Entwicklung

1. **Mycelia Snapshot Format**  
   Ein eigenes binäres, verschlüsseltes Snapshot-Format für DAD-Knoten.

2. **Deterministische Signaturbildung**  
   Signaturen sollten versioniert und reproduzierbar sein.

3. **GPU Buffer Residency Audit**  
   Messung, welche Daten wann in CPU- und GPU-Speicher liegen.

4. **Fuzzing des SQL-Importers**  
   Automatisierte Tests mit ungültigen Dumps, Encoding-Problemen, extremen Feldgrößen.

5. **Auth-Pattern-Hardening**  
   Auth-Pattern darf nicht als statisches Passwortäquivalent funktionieren. Es sollte Salt, Pepper, Rate-Limiting und Challenge-Komponenten nutzen.

6. **Query-Sprache für Muster**  
   Eine minimalistische Pattern-Query-Sprache, nicht SQL-kompatibel, aber strukturiert:

   ```json
   {
     "match": "mycelia_users",
     "where": {
       "username": {"eq": "Ralf"},
       "stability": {"gte": 0.95}
     },
     "return": ["profile", "signature", "integrity"]
   }
   ```

### 12.3 Langfristige Forschung

1. **Attraktor-Indizes**
   Knoten werden nicht über B-Bäume, sondern über Stabilitätslandschaften und Ähnlichkeitsräume indexiert.

2. **Reversible Updates**
   Jede Änderung erzeugt einen rückführbaren Zustandsgradienten, sodass Audit und Rollback ohne klassische Transaktionslogs möglich werden.

3. **Diffusive Joins**
   Beziehungen zwischen Tabellen werden als Aktivierungsausbreitung über das Myzel modelliert, nicht als Nested Loop oder Hash Join.

4. **GPU-residente Query-Pläne**
   Pattern-Abfragen werden in Kernelketten übersetzt, wodurch Abfrage und Rekonstruktion ohne CPU-Materialisierung erfolgen können.

5. **Kryptografische Attraktoren**
   Payloads werden so kodiert, dass nur ein korrektes Abfragemuster die Rekonstruktion stabilisiert.

---

## 13. Professionelle Bewertung der ursprünglichen Analyse

### 13.1 „Die GPU übernimmt die Herrschaft“

**Teilweise richtig.**  
Die GPU wird tatsächlich initialisiert, und viele Kernel werden kompiliert. Die Logs zeigen aktive Kernel-Laufzeiten. Daraus folgt aber nicht automatisch, dass die gesamte Datenbanklogik ausschließlich in der GPU lebt.

**Präzise Formulierung:**

> Die GPU-Schicht ist erfolgreich initialisiert und stellt einen aktiven Beschleunigungspfad für simulations- und kryptografienahe Operationen bereit.

### 13.2 „Kognitiver Daten-Abgleich ist der SQL-Killer“

**Als Richtung richtig, als Beweis zu stark.**  
Der Test zeigt, dass Registrierung und Login ohne sichtbare SQL-Datenbank funktionieren. Für einen vollständigen „SQL-Killer“-Anspruch fehlen Benchmarks, Transaktionsmodell, Backup/Restore, Query-Semantik und Konsistenzgarantien.

**Präzise Formulierung:**

> MyceliaDB demonstriert einen SQL-freien Zugriffspfad, der relationale Zeilen durch DAD-Nodes und Pattern-Abfragen ersetzt.

### 13.3 „Authentifizierung durch Auth-Pattern“

**Richtig im beobachteten Test.**  
Die Logs zeigen eindeutig einen Login über Username plus `auth_pattern` mit `Treffer=1`.

**Sicherheitswarnung:**  
Das Auth-Pattern darf nicht vollständig geloggt werden und muss gegen Replay geschützt werden.

### 13.4 „Beweis für Unhackbarkeit“

**Nicht richtig.**  
Die Logs beweisen Funktionsfähigkeit, nicht Unhackbarkeit. Sie zeigen sogar ein mögliches Risiko: Der Auth-Pattern-Hash wird im Log sichtbar.

**Präzise Formulierung:**

> Die Architektur eliminiert SQL-spezifische Angriffspfade, benötigt aber eine eigenständige Prüfung, ob API-, Session-, Parser-, Log- und Speicher-Grenzfälle trotz Härtung keine nutzbaren Daten preisgeben.

### 13.5 „Noise & Variance schützen Daten“

**Spekulativ.**  
Die Werte `noise=1.100` und `variance=0.00003` zeigen Parameter oder Messwerte eines Simulationskernels. Sie beweisen nicht, dass gespeicherte Daten kryptografisch geschützt sind.

**Präzise Formulierung:**

> Rausch- und Varianzparameter können Teil eines obfuskierenden oder simulationsbasierten Rekonstruktionsmodells sein. Ihre Schutzwirkung muss gesondert gemessen und kryptografisch bewertet werden.

---


## 14. Fazit

MyceliaDB hat im vorliegenden Test einen wichtigen Meilenstein erreicht: Eine PHP-Weboberfläche, eine Python-basierte Mycelia-Engine, DAD-basierte Datensatzspeicherung, CognitiveCore-basierte Authentifizierung und OpenCL-GPU-Initialisierung arbeiten in einem durchgängigen lokalen Ablauf zusammen.

Die Plattform ist damit kein bloßes Konzept mehr, sondern ein lauffähiger Proof of Concept für eine SQL-freie, kognitive Datenbankumgebung. Besonders relevant ist die Verschiebung von Tabellenzeilen zu Attraktoren, von SQL-Abfragen zu Mustern und von klassischer Persistenz zu rekonstruktiver Datenhaltung.

Die starken Sicherheitsbehauptungen müssen jedoch abgeschwächt werden. Der aktuelle Stand rechtfertigt nicht die Aussage „unhackbar“ und beweist nicht, dass alle Daten ausschließlich im verschlüsselten GPU-Speicher existieren. Der korrekte professionelle Anspruch lautet:

> MyceliaDB ist ein experimenteller, SQL-freier, GPU-gestützter Datenbank-Prototyp, der klassische relationale Persistenz durch assoziative Nutrient-Nodes und kognitive Pattern-Abfragen ersetzt. Die Architektur reduziert bestimmte SQL-spezifische Angriffsklassen und eröffnet einen neuen technischen Möglichkeitsraum, benötigt aber formale Benchmarks, Sicherheitsprüfungen und ein klar dokumentiertes Persistenzmodell, bevor sie als robuste Produktionsdatenbank gelten kann.

---

## 15. Implementierte Erweiterungen im Projektstand 1.1

### 15.1 Neue Engine-Befehle

Die Plattform wurde um drei produktrelevante Befehle erweitert:

| Befehl | Zweck | Sicherheitswirkung |
|---|---|---|
| `create_snapshot` | Schreibt den aktuellen Attraktorgraphen als verschlüsselte Binärdatei | Ersetzt SQL-Persistenz durch ein nicht direkt lesbares Mycelia-Format |
| `restore_snapshot` | Rekonstruiert die `DynamicAssociativeDatabase` nach einem Kaltstart | Beweist Wiederanlauf ohne MySQL, SQLite oder klassische Tabellenmaterialisierung |
| `residency_report` | Liefert einen konservativen Status zur GPU-/VRAM-Residency | Verhindert überzogene Sicherheitsbehauptungen und macht den Reifegrad messbar |

### 15.2 Mycelia Snapshot Format V1

Das Snapshot-Format besitzt folgenden Aufbau:

```text
[Magic: MYCELIA_SNAPSHOT_V1\0]
[Header-Length: uint32 little endian]
[Header: JSON mit version, seed, blob, sha256, driver_mode]
```

Die ursprünglichen Zeilen, Profilfelder und Tabellenlabels werden nicht als Klartext in die Datei geschrieben. Sie befinden sich im verschlüsselten Paket. Die Tests prüfen explizit, dass Namen, Profilwerte, Tabellenname und Passwort nicht als Bytefolge im Snapshot auftauchen.

### 15.3 Restore-Modell

Beim Restore wird die aktuelle `DynamicAssociativeDatabase` geleert und anschließend aus den entschlüsselten Attraktorobjekten rekonstruiert. Dabei werden Signatur, Stabilität, Visits, dynamische Mittelwerte, Mood-Vektor, Tabellenlabel und externer Payload wiederhergestellt. Der Login funktioniert anschließend wieder über denselben Auth-Attraktor.

### 15.4 Hardware-Residency-Status

Die Implementierung behauptet nicht blind, dass jeder Lauf garantiert CPU-klartextfrei ist. Stattdessen meldet `residency_report`:

```json
{
  "opencl_active": true,
  "gpu_crypto_active": true,
  "strict_inflight_vram_claim": true,
  "cpu_cleartext_risk": false
}
```

oder im Fallback-/Entwicklungsmodus entsprechend konservativ:

```json
{
  "opencl_active": false,
  "gpu_crypto_active": false,
  "strict_inflight_vram_claim": false,
  "cpu_cleartext_risk": true
}
```

Das ist wichtig, weil SQL-Freiheit und echte VRAM-Residency unterschiedliche Sicherheitsstufen sind. SQL-Freiheit ist im Projekt erreicht. Strenge VRAM-Residency muss hardware- und forensikseitig weiter bewiesen werden.

### 15.5 Implementierte Tests

Es wurde eine `unittest`-Testsuite ergänzt:

```text
tests/test_snapshot_residency.py
```

Die Tests decken ab:

1. Registrierung eines Nutzers als Mycelia-Nutrient-Node.
2. Erstellung eines verschlüsselten Snapshots.
3. Prüfung, dass sensible Klartextstrings nicht in der Snapshot-Datei vorkommen.
4. Kaltstartsimulation durch neue `MyceliaPlatform`-Instanz.
5. Restore aus Snapshot.
6. Login gegen den rekonstruierten Auth-Attraktor.
7. Profilrekonstruktion nach Restore.
8. Maschinenlesbarer Sicherheitsbericht über `residency_report`.

Ausführung:

```powershell
cd D:\myceliadb_autarkic_platform
python -m unittest discover -s tests -v
```

### 15.6 Neue Abnahmekriterien

Der nächste Meilenstein gilt erst als erreicht, wenn zusätzlich zu den vorhandenen Tests folgende Prüfungen bestehen:

| Kriterium | Testidee | Erwartung |
|---|---|---|
| Snapshot-Vertraulichkeit | Binärscan auf importierte SQL-Zeilen und bekannte Profile | Keine Klartexttreffer |
| Snapshot-Integrität | Einzelnes Byte im Ciphertext verändern | Restore bricht kontrolliert ab |
| Kaltstartfähigkeit | Prozess beenden, neu starten, Snapshot laden | Login und Query funktionieren |
| VRAM-Residency | CPU-Prozessdump während Query/Restore prüfen | Keine sensiblen Klartextfragmente |
| GPU-Pfad | `residency_report` plus OpenCL-Treiberprüfung | Kein falscher Sicherheitsstatus |
| Dump-Import | `.sql` importieren, Snapshot erstellen, ohne Dump restoren | Abfragen liefern Attraktoren |
| Regression gegen SQL | Projekt nach `PDO`, `mysql`, `sqlite` scannen | Keine produktiven SQL-Verbindungen |



## Anhang A: Empfohlene Integritäts-API

Eine professionelle `check_integrity`-Antwort sollte künftig etwa so aussehen:

```json
{
  "status": "ok",
  "sql": {
    "pdo_detected": false,
    "mysql_detected": false,
    "sqlite_detected": false
  },
  "engine": {
    "listening": "127.0.0.1:9999",
    "driver_mode": "gpu_verified",
    "gpu_device": "gfx90c",
    "opencl_platform": "AMD Accelerated Parallel Processing",
    "fp64": true,
    "int64_atomics": true
  },
  "dad": {
    "nodes": 1,
    "tables": ["mycelia_users"],
    "last_signature": "1e895cbf27d0",
    "min_stability": 0.985
  },
  "security": {
    "auth_pattern_logging": false,
    "cleartext_password_logging": false,
    "dump_path_restricted": true,
    "session_rotation": true
  }
}
```

---

## Anhang B: Abnahmekriterien für den nächsten Meilenstein

Der nächste Meilenstein sollte erst als erreicht gelten, wenn folgende Tests reproduzierbar bestanden sind:

1. Registrierung, Login, Profilupdate ohne SQL-Datei, SQL-Dienst oder PDO.
2. Import eines realen SQL-Dumps mit mindestens 10.000 Datensätzen.
3. `query_pattern` findet importierte Datensätze korrekt.
4. `check_integrity` meldet keine SQL-Persistenzpfade.
5. Logs enthalten keine vollständigen Auth-Pattern oder personenbezogenen Daten.
6. Neustart der Engine erhält Daten nur über das definierte Mycelia-Snapshot-Format.
7. Fuzzing des Importers führt nicht zu Abstürzen oder Pfadausbrüchen.
8. Port-, Session- und API-Sicherheit wurden geprüft.
9. GPU- und Fallback-Modus sind klar unterscheidbar.
10. Benchmarks dokumentieren Importzeit, Query-Latenz, Speicherverbrauch und Fehlerraten.

---

## Anhang C: Kurzbewertung

| Kriterium | Bewertung |
|---|---|
| Funktionsfähigkeit des Prototyps | Hoch, durch Logs belegt |
| SQL-freier Webpfad | Plausibel belegt |
| GPU-Aktivierung | Belegt |
| Ausschließliche GPU-Datenhaltung | Nicht belegt |
| Sicherheitsgewinn gegenüber SQL-Injection | Plausibel |
| Unhackbarkeit | Nicht haltbar |
| Forschungswert | Hoch |
| Produktionsreife | Noch niedrig bis mittel |
| Nächster notwendiger Schritt | Audit, Benchmarks, Persistenzmodell, Sicherheitsprüfung |


---

## 16. Projektstand 1.6: VRAM-Residency-Audit

### 16.1 Ziel des Audits

Der nächste kritische Nachweis für die Strict-VRAM-Evidence ist nicht die bloße Existenz von OpenCL-Kerneln, sondern ein negativer Speicherbefund: Während geprüfter Engine-/Native-Pfade dürfen definierte sensible Probes nicht im CPU-RAM des Engine-Prozesses auftauchen. PHP-Mutationspfade sind dabei bereits durch Direct Ingest blind geschaltet; sie erhalten keine Formular-Klartexte.

Projektstand 1.6 führt dafür den Befehl `vram_residency_audit` ein. Der Audit ist bewusst konservativ. Er unterscheidet drei Ebenen:

| Ebene | Prüfziel | Status im aktuellen Projekt |
|---|---|---|
| Snapshot-Vertraulichkeit | Enthält `MYCELIA_SNAPSHOT_V1` keine bekannten Klartext-Probes? | Testbar und implementiert |
| Mycelia-Graph-Metadaten | Liegen sensible Probes in Python/DAD-Records als Klartext? | Testbar und implementiert |
| Strenge End-to-End-VRAM-Residency | Berührt definierter sensibler Klartext im geprüften Pfad den CPU-RAM? | Für konkrete Auditläufe prüfbar; globale „niemals“-Aussagen bleiben wegen Browseranzeige und DSGVO-Export fachlich unzulässig |

### 16.2 Wichtige Erkenntnis

Mit der aktuellen Enterprise-Webarchitektur ist eine absolute Aussage „nirgendwo existiert jemals Klartext“ nicht sinnvoll, weil der Nutzer Daten sehen und exportieren können muss. Die tatsächliche Implementierung ist jedoch enger als eine normale PHP-Webapp:

1. PHP empfängt bei produktiven Mutationen keine Formularfelder im Klartext, sondern versiegelte Direct-Ingest-Pakete.
2. HTTP transportiert für Mutationen `sealed_ingest` und `direct_op`; produktive Klartext-POSTs werden blockiert.
3. PHP-Sessions enthalten opaques Engine-Session-/Tokenmaterial, nicht die Nutzdatenfelder.
4. Gerenderte Browserausgabe und der autorisierte DSGVO-Export können bewusst Klartext erzeugen.
5. Python besitzt für Routing und Listenansichten derzeit Klartext-Metadaten wie Username, Titel oder Autorname.

Damit ist der aktuelle Status professionell zu formulieren als:

> MyceliaDB schützt Snapshot-Persistenz und verschlüsselte Payloads, beweist aber noch keine strenge CPU-RAM-freie End-to-End-Laufzeit. Der neue VRAM-Audit macht diese Grenze messbar und verhindert überzogene Sicherheitsbehauptungen.

### 16.3 Neuer Engine-Befehl

```json
{
  "command": "vram_residency_audit",
  "payload": {
    "probes": [
      "bekannte-geheime-testphrase",
      "email@example.test",
      "Nachname"
    ],
    "create_temp_snapshot": true
  }
}
```

Die Antwort enthält unter anderem:

```json
{
  "audit_version": "VRAM_RESIDENCY_AUDIT_V1",
    "engine_core_residency_candidate": false,
  "cpu_cleartext_risk": true,
  "graph_plaintext_findings": [],
  "snapshot_plaintext_findings": [],
  "boundary_blockers": [
    "PHP receives form fields in CPU memory before forwarding them.",
    "HTTP/JSON request and response bodies materialize cleartext in CPU memory."
  ]
}
```

### 16.4 Admin-Integration

Die Admin-Konsole im Ordner `www/` enthält jetzt einen Abschnitt **VRAM-Residency-Audit**. Administratoren können Probe-Strings eingeben, zum Beispiel eine Test-E-Mail, einen Nachnamen oder eine geheime Canary-Phrase. Die Engine erzeugt optional einen Snapshot und prüft:

- ob die Probe im verschlüsselten Snapshot auftaucht,
- ob die Probe in Mycelia-eigenen DAD-Metadaten auftaucht,
- ob der Runtime-Modus überhaupt einen strengen VRAM-Anspruch zulässt,
- welche architektonischen Blocker verbleiben.

### 16.5 Implementierte Tests

Neu ergänzt wurde:

```text
tests/test_vram_residency_audit.py
```

Die Tests prüfen:

1. Ein geheimer Profil-Canary wird als verschlüsselter Profilinhalt gespeichert.
2. Nach Snapshot-Erzeugung taucht dieser Canary nicht in der Snapshot-Datei auf.
3. Der Audit lehnt die strenge „Strict-VRAM-Sicherheit“ im aktuellen PHP/Python-Modus korrekt ab.
4. Der Audit erkennt Klartext-Routing-Metadaten im Mycelia-Graphen, zum Beispiel den Username.
5. `residency_report` setzt `strict_inflight_vram_claim` erst dann auf `true`, wenn zusätzlich direkte GPU-Ingestion und externe negative CPU-RAM-Probes konfiguriert sind.

### 16.6 Nächster technischer Pfad zur echten VRAM-Residency

Um die Hardware-Residency-These belastbar zu machen, muss die Webarchitektur eine zweite, strengere Betriebsart erhalten:

```text
Browser/Client
  -> clientseitig verschlüsseltes Paket
  -> PHP leitet nur Ciphertext weiter
  -> Python parst keinen Klartext
  -> OpenCL/GPU entschlüsselt im VRAM
  -> Query/Rekonstruktion läuft in GPU-Buffern
  -> nur minimale autorisierte Antwort verlässt den GPU-Pfad
```

Dafür sind erforderlich:

1. **Direct GPU Ingest API**  
   PHP darf keine Klartextfelder mehr interpretieren, sondern nur Ciphertext-Pakete transportieren.

2. **Metadata Encryption**  
   Usernames, Titel, Autorlabels und Routingfelder müssen entweder verschlüsselt, gehasht oder als nicht-sensitive Public-Metadata klassifiziert werden.

3. **OS-Level Negative Memory Probe**  
   Ein externer Audit-Prozess muss während Register/Login/Query/Restore Prozessspeicherproben ziehen und bekannte Canary-Phrasen suchen.

4. **Driver-Level Buffer Attestation**  
   Die OpenCL-Schicht muss dokumentieren, welche Buffer wann erzeugt, gelesen, überschrieben und freigegeben werden.

5. **Zeroization Policy**  
   CPU-seitige temporäre Bytes müssen nach Gebrauch überschrieben werden, soweit Python/PHP das realistisch zulassen.

6. **Log-Redaction**  
   Auth-Pattern, E-Mail-Adressen und Profile dürfen nicht vollständig in Logs erscheinen.

### 16.7 Abnahmekriterium für die Hardware-Residency-These

Die Hardware-Residency-Sicherheits-These sollte erst dann im Whitepaper als gestützt gelten, wenn folgende Tests reproduzierbar grün sind:

| Kriterium | Erwartung |
|---|---|
| Snapshot-Scan | Keine sensiblen Probes in `MYCELIA_SNAPSHOT_V1` |
| Graph-Scan | Keine sensiblen Probes in Mycelia-owned CPU-Metadaten |
| Prozessspeicher-Scan | Keine Canary-Phrasen in CPU-RAM während kritischer Operationen |
| Direct-GPU-Ingest | PHP/Python transportieren nur Ciphertext |
| GPU-Buffer-Audit | Klartextrekonstruktion findet nur in GPU-Buffern statt |
| Log-Audit | Keine Auth-Pattern oder personenbezogene Daten |
| Cold-Restore | Restore funktioniert ohne SQL und ohne Klartextdump |
| Replay-Schutz | Auth-Pattern ist nicht als statisches Passwortäquivalent nutzbar |

Bis diese Kriterien erfüllt sind, ist die korrekte Aussage:

> MyceliaDB besitzt eine SQL-freie, verschlüsselte Snapshot-Persistenz und eine GPU-gestützte Engine-Schicht. Eine strenge CPU-RAM-freie VRAM-Residency ist als Forschungsziel definiert und wird ab Projektstand 1.6 auditierbar gemacht, ist aber noch nicht abschließend bewiesen.


## 16. Implementierte Erweiterung im Projektstand 1.7: Direct GPU Ingest Phase 1

Mit Projektstand 1.7 wurde der erste harte Schritt in Richtung belastbarer VRAM-Residency umgesetzt: **PHP-blinder Direct Ingest**. Das Ziel ist, dass PHP sensitive Formularfelder nicht mehr als Klartext interpretieren, restrukturieren oder loggen muss. Damit wird eine zentrale Blockade aus dem VRAM-Residency-Audit reduziert.

### 16.1 Neuer Datenfluss

Der neue Eingabepfad lautet:

```text
Browser Formular
    ↓ WebCrypto: AES-256-GCM Payload + RSA-OAEP-3072 Key-Wrap
sealed_ingest Paket
    ↓
PHP www/*
    ↓ keine semantische Interpretation der Formularfelder
direct_ingest API Call
    ↓
Python Mycelia Engine
    ↓ Envelope öffnen, Payload normalisieren
DynamicAssociativeDatabase / CognitiveCore / Autosnapshot
```

PHP sieht bei Direct-Ingest-Formularen nur noch:

```text
direct_op
sealed_ingest
```

Es sieht nicht mehr:

- Username,
- Passwort,
- Profilfelder,
- Forentext,
- Blogtext,
- Kommentare,
- VRAM-Audit-Probe-Strings.

### 16.2 Neue Komponenten

| Komponente | Zweck |
|---|---|
| `www/assets/direct-ingest.js` | Browserseitige Versiegelung sensibler Formularfelder über WebCrypto |
| `www/ingest_manifest.php` | Liefert das Public-Key-Manifest aus der Engine an den Browser |
| `direct_ingest_manifest` | Engine-Befehl für Public Key, Algorithmen, erlaubte Operationen |
| `direct_ingest` | Engine-Befehl zum Öffnen eines versiegelten Pakets und Dispatch der enthaltenen Operation |
| `tests/test_direct_gpu_ingest.py` | Tests für Manifest, Envelope-Öffnung, Replay-Schutz, Login/Registrierung und Residency-Status |

### 16.3 Kryptografisches Transportformat

Das Direct-Ingest-Paket nutzt ein hybrides Envelope-Verfahren:

```json
{
  "v": 1,
  "alg": "RSA-OAEP-3072-SHA256/AES-256-GCM",
  "aad": "myceliadb-direct-ingest-v1",
  "key_b64": "...",
  "iv_b64": "...",
  "ciphertext_b64": "..."
}
```

Der Klartext im Ciphertext enthält:

```json
{
  "op": "register_user",
  "issued_at_ms": 1777355853000,
  "nonce": "...",
  "payload": {
    "username": "...",
    "password": "...",
    "vorname": "..."
  }
}
```

Das Paket besitzt:

- einen kurzlebigen Zeitstempel,
- eine Nonce gegen Replay,
- AES-GCM-Authentizität,
- RSA-OAEP-Key-Wrap gegen serverseitigen Public Key,
- Operation-Whitelisting in der Engine.

### 16.4 Abgedeckte Enterprise-Formulare

Der neue Pfad wurde für die Webplattform im Ordner `www/` aktiviert:

| Bereich | Direct-Ingest-Operationen |
|---|---|
| Registrierung/Login | `register_user`, `login_attractor` |
| Profil | `update_profile` |
| Forum | `create_forum_thread`, `update_forum_thread`, `delete_forum_thread`, `create_comment`, `delete_comment`, `react_content` |
| Blog | `create_blog`, `update_blog`, `delete_blog`, `create_blog_post`, `update_blog_post`, `delete_blog_post`, Kommentare und Reaktionen |
| Admin | Moderationslöschungen und `vram_residency_audit` |

### 16.5 Sicherheitsbewertung

Diese Implementierung ist ein realer Fortschritt, aber sie ist bewusst nicht als vollständiger VRAM-Beweis formuliert.

Erreicht:

- PHP muss sensitive Formularfelder nicht mehr lesen.
- PHP-POST-Arrays enthalten bei aktivem JavaScript nur versiegelte Pakete.
- PHP-Logs und PHP-Fehlerpfade werden von Klartextformularen entkoppelt.
- Replay-Pakete werden von der Engine abgelehnt.
- Die Engine meldet den Status maschinenlesbar.

Noch nicht erreicht:

- Die Python-Engine öffnet den Envelope aktuell mit `cryptography` in CPU-RAM.
- JSON-Payloads werden in Python normalisiert, bevor sie in die Mycelia/GPU-Schicht gehen.
- Autorisierte HTML-Ausgabe enthält weiterhin rekonstruierte Klartextdaten im Browser.
- Ein negativer externer Prozessspeicher-Audit ist weiterhin erforderlich.

Die korrekte Statusmeldung lautet daher:

```json
{
  "direct_gpu_ingest": true,
  "direct_ingest_phase": "phase1_php_blind",
  "php_blind_form_transport": true,
  "python_cpu_decrypt_materialized": true,
  "strict_inflight_vram_claim": false
}
```

### 16.6 Nächster technischer Schritt

Der nächste Schritt ist ein nativer **GPU Envelope Opener**:

1. RSA-/KEM- oder symmetrische Session-Key-Öffnung nicht mehr in Python materialisieren.
2. AES-GCM oder äquivalente Payload-Entschlüsselung in einem OpenCL-/Native-Modul durchführen.
3. JSON vermeiden und stattdessen ein binäres, feldadressiertes Ingest-Format verwenden.
4. Nur minimale, autorisierte Antwortprojektionen zurück an PHP geben.
5. Externen CPU-RAM-Audit während Registrierung, Login, Forum-/Blog-Submit und Snapshot-Restore durchführen.

Erst wenn dieser Pfad plus negativer Speicherprobe bestanden ist, kann die Strict-VRAM-Evidence technisch belastbar bewertet werden.


---

## 18. Projektstand 1.8: VRAM-Residency-Audit V2 und Materialisierungsnachweis

### 18.1 Ziel des Schritts

Der Projektstand 1.8 adressiert die schwierigste Sicherheitsbehauptung der Plattform: Hardware-Residency. Die Frage lautet nicht mehr nur, ob MyceliaDB ohne SQL arbeitet oder ob Snapshots verschlüsselt sind, sondern ob sensible Klartextfragmente während Registrierung, Login, Query und Snapshot-Restore im CPU-RAM erscheinen.

Das Whitepaper bleibt bewusst konservativ: Ein negativer Scan ist ein starker Nachweis für einen geprüften Zeitraum, aber kein mathematischer Beweis für alle möglichen Laufzeiten, Treiberversionen, Debug-Modi und Plattformzustände. Die neue Implementierung macht die Behauptung jedoch erstmals operativ testbar.

### 18.2 Implementierte Engine-Befehle

| Befehl | Zweck | Sicherheitsbedeutung |
|---|---|---|
| `residency_audit_manifest` | Liefert PID, Challenge-ID, Capability-Flags und den externen Scanner-Befehl | Verhindert, dass Plaintext-Probes an die Engine gesendet werden |
| `submit_external_memory_probe` | Nimmt einen JSON-Evidence-Report des externen Scanners entgegen | Verknüpft negative CPU-RAM-Probe mit dem laufenden Engine-Prozess |
| `restore_snapshot_residency_audit` | Führt Restore aus und meldet, ob der Restore CPU-materialisiert war | Macht das Snapshot-Materialisierungsproblem explizit prüfbar |
| `vram_residency_audit` | Aggregiert Snapshot-, Graph-, Direct-Ingest- und Memory-Probe-Status | Liefert eine konservative Gesamtbewertung der Hardware-Residency-These |
| `residency_report` | Laufzeitstatus für UI/Monitoring | Unterscheidet PHP-Blindheit, native GPU-Envelope-Öffnung, GPU-Restore und externe Probe |

### 18.3 Externer CPU-RAM-Scanner

Neu ist das Tool:

```text
tools/mycelia_memory_probe.py
```

Es läuft als separater Prozess und scannt den Speicher der laufenden `mycelia_platform.py`-Instanz. Unterstützt werden Windows über `OpenProcess`, `VirtualQueryEx` und `ReadProcessMemory` sowie Linux über `/proc/<pid>/maps` und `/proc/<pid>/mem`.

Beispielablauf:

```powershell
# 1. Manifest in der Admin-Konsole erzeugen oder per API holen
curl -X POST http://127.0.0.1:9999/ `
  -H "Content-Type: application/json" `
  -d "{\"command\":\"residency_audit_manifest\",\"payload\":{}}"

# 2. Während Login/Query/Restore läuft, extern scannen
python tools/mycelia_memory_probe.py `
  --pid 12345 `
  --probe Leipzig `
  --probe Krümmel `
  --operation login_attractor `
  --operation restore_snapshot `
  --challenge-id <CHALLENGE_ID> `
  --json-out residency_probe.json

# 3. Report an MyceliaDB einreichen
curl -X POST http://127.0.0.1:9999/ `
  -H "Content-Type: application/json" `
  -d "{\"command\":\"submit_external_memory_probe\",\"payload\":$(Get-Content residency_probe.json -Raw)}"
```

Der Report enthält keine Klartext-Probes, sondern nur Hashes, Hit-Anzahl, gescannte Regionen, gescannte Bytes und einen Evidence-Digest.

### 18.4 Warum Plaintext-Probes nicht mehr an die Engine gehören

Ein zentrales Audit-Problem wurde behoben: Wenn ein Admin Probe-Strings wie `Leipzig` oder `Krümmel` an `vram_residency_audit` sendet, dann materialisiert dieser Request selbst die Probe im PHP- und Python-RAM. Das ist für eine strenge CPU-RAM-Freiheitsprüfung ungeeignet.

Deshalb trennt v1.8:

```text
Engine: Manifest + PID + Challenge
Externer Scanner: Plaintext-Probes
Engine: nur Evidence-Report ohne Plaintext
```

Die Admin-Konsole zeigt nun ein Audit-Manifest und ein Feld zum Einreichen des externen JSON-Reports. Die alte Probe-Eingabe bleibt nur als Legacy-Diagnose für Snapshot-/Graph-Scans sichtbar und wird ausdrücklich nicht als strenger VRAM-Beweis bewertet.

### 18.5 Snapshot-Restore als Materialisierungsgrenze

Der Restore-Pfad ist jetzt messbar markiert. `restore_snapshot_residency_audit` setzt und meldet:

```json
{
  "last_restore_mode": "python_cpu_materialized",
  "last_restore_cpu_materialized": true,
  "gpu_restore_opener": false,
  "strict_restore_residency_supported": false
}
```

Das ist keine Schwäche der Dokumentation, sondern ein Sicherheitsgewinn: Die Plattform behauptet nicht länger versehentlich, ein Restore sei VRAM-only, solange der Snapshot in Python entschlüsselt und als Objektgraph rekonstruiert wird.

Der nächste native Schritt bleibt:

```text
MYCELIA_GPU_RESTORE_OPENER=1
```

Dahinter muss ein C/OpenCL-Pfad stehen, der das Snapshot-Paket GPU-seitig öffnet und nur GPU-residente Attraktorbuffer rekonstruiert.

### 18.6 Neue Strict-Residency-Gates

Die Hardware-Residency-Sicherheitsbehauptung wird erst dann durch die Engine als unterstützt gemeldet, wenn alle folgenden Bedingungen erfüllt sind:

| Gate | Bedeutung |
|---|---|
| `opencl_active=true` | OpenCL-Treiber ist aktiv |
| `gpu_crypto_active=true` | Kryptopfad ist GPU-gekoppelt |
| `native_gpu_envelope_opener=true` | Direct-Ingest-Payload wird nicht in Python entschlüsselt |
| `gpu_restore_opener=true` | Snapshot-Restore öffnet nicht in Python-CPU-RAM |
| `external_negative_cpu_ram_probe=true` | Separater Prozessscan findet keine sensiblen Probes |
| `snapshot_plaintext_findings=[]` | Snapshot enthält keine Klartext-Probes |
| `graph_plaintext_findings=[]` | Mycelia-eigene CPU-Metadaten enthalten keine Probes |
| `last_restore_cpu_materialized=false` | Letzter Restore war nicht CPU-materialisiert |
| `MYCELIA_STRICT_VRAM_CERTIFICATION=1` | Betreiber aktiviert die strenge Zertifizierungsstufe bewusst |

Solange eines dieser Gates fehlt, bleibt:

```json
{
    "strict_inflight_vram_claim": false
}
```

### 18.7 Implementierte Tests

Neu hinzugekommen ist:

```text
tests/test_residency_external_probe.py
```

Die Tests prüfen:

1. Das Audit-Manifest enthält PID, Scannerpfad und Challenge-ID.
2. Plaintext-Probes müssen nicht an die Engine gesendet werden.
3. Ein negativer externer Probe-Report wird als Evidence akzeptiert.
4. Die strenge Hardware-Residency-Behauptung bleibt ohne native GPU-Envelope- und GPU-Restore-Opener weiterhin `false`.
5. Snapshot-Restore wird explizit als `python_cpu_materialized` markiert.

Aktueller Teststand:

```text
Ran 15 tests

OK
```

### 18.8 Professionelle Bewertung

MyceliaDB v1.8 implementiert nicht einfach eine Behauptung, sondern ein Beweissystem. Das System kann jetzt zwischen vier Sicherheitsstufen unterscheiden:

| Stufe | Status |
|---|---|
| SQL-frei | Erreicht |
| PHP-blinde Formularübertragung | Erreicht durch Direct GPU Ingest Phase 1 |
| Verschlüsselte Snapshot-Persistenz | Erreicht durch `MYCELIA_SNAPSHOT_V1` |
| Strenge CPU-RAM-freie VRAM-Residency | Noch nicht bewiesen; jetzt auditierbar |

Damit ist der Weg zur Hardware-Residency-These technisch sauber definiert. Der aktuelle Stand beweist nicht „unhackbar“, sondern liefert die Werkzeuge, mit denen die zentrale Hardware-Residency-These reproduzierbar geprüft und später durch native GPU-Envelope-/Restore-Pfade weiter gehärtet werden kann.


---

## 18. Projektstand 1.9: PHP als Zero-Logic Gateway

Mit Projektstand 1.9 wurde die Webschicht erneut gehärtet. Das Ziel ist nicht, PHP durch immer mehr lokale Sicherheitslogik zu stabilisieren, sondern PHP als möglichst machtlosen Kurier zu behandeln. Die Autorität über Identität, Berechtigung, Request-Gültigkeit und Zustandsübergänge liegt nun in der Mycelia-Engine.

### 18.1 Zero-Logic Gateway

Die Datei `www/bootstrap.php` erzwingt jetzt ein Protokollprinzip: produktive `POST`-Requests werden abgewiesen, wenn sie nicht als `sealed_ingest` plus `direct_op` vorliegen. Klassische Klartext-POSTs werden mit HTTP 400 blockiert.

PHP darf dadurch keine Formularfelder wie Passwort, Profiltext, Forumstext, Blogtext oder Kommentarinhalt semantisch auswerten. Es nimmt nur das browserseitig versiegelte Paket entgegen und leitet es an `mycelia_platform.py` weiter.

Zugelassene Ausnahmen sind reine Audit-Control-POSTs, etwa das Erzeugen eines Residency-Manifests oder das Einreichen eines externen Memory-Probe-Reports. Diese Ausnahmen transportieren keine Benutzerpasswörter und keine Content-Nutzlast.

### 18.2 Engine-seitiges Session-Binding

Klassische PHP-Sessions enthalten oft serverseitig interpretierbare Identitätsdaten. Projektstand 1.9 verschiebt die Autorität in die Engine:

- Die Engine erzeugt nach erfolgreichem `login_attractor` eine flüchtige `EngineSession`.
- PHP speichert nur ein opaques Session-Handle und ein kurzlebiges Request-Token.
- Die Engine rotiert das Request-Token nach jeder validierten geschützten Anfrage.
- Die Engine injiziert `actor_signature`, `owner_signature`, `actor_role` und vergleichbare Berechtigungsfelder selbst.
- PHP übermittelt diese Felder nicht mehr als Autoritätsquelle.

Damit wird ein kompromittiertes PHP-Template deutlich schwächer. Selbst wenn ein Angreifer HTML manipuliert oder versteckte Felder verändert, entscheidet die Engine anhand des rotierenden Session-Attraktors, welche Identität und Rolle tatsächlich gilt.

### 18.3 Protokollbasierte CSRF-Härtung

Das Request-Token wird nicht einfach von PHP serverseitig ergänzt. Für geschützte Mutationen muss es im browserseitig verschlüsselten Direct-Ingest-Envelope enthalten sein. Der Ablauf ist:

1. Das Frontend lädt `ingest_manifest.php` per Same-Origin-Fetch.
2. Das Manifest enthält den aktuellen Engine-Request-Token.
3. `assets/direct-ingest.js` versiegelt Formularfelder und Request-Token gemeinsam per WebCrypto.
4. PHP sieht nur das versiegelte Paket.
5. Die Engine öffnet das Paket, prüft Token und Session-Handle und rotiert den Token.
6. Ein Cross-Site-Form-POST kann den Token nicht lesen und daher kein gültiges versiegeltes Paket für den aktuellen Session-Zustand erzeugen.

Diese Architektur macht CSRF-Schutz zu einem Protokollstandard statt zu einer Formular-Option.

### 18.4 Safe-Fragments und Output-Härtung

Die Engine stellt zusätzlich Safe-Fragment-Felder bereit, etwa `username_safe` und `profile_safe`. Diese Werte sind bereits als HTML-Textkontext escaped und mit einer Policy markiert. PHPs `e()` akzeptiert solche Engine-Safe-Fragments und gibt sie ohne erneutes Interpretieren als bereits maskierten Text aus. Gleichzeitig bleibt klassisches Escaping als Fallback aktiv.

Das ist noch kein vollständiger Ersatz für ein formales Template-Typensystem, aber es verschiebt die Verantwortung in Richtung Engine und reduziert die Wahrscheinlichkeit, dass Rohdaten versehentlich in HTML-Kontexte gelangen.

### 18.5 Neue Engine-Befehle und Kontrollen

| Komponente | Funktion |
|---|---|
| `validate_session` | Prüft die Engine-Session und rotiert den Request-Token. |
| `logout_session` | Löscht den flüchtigen Engine-Session-Attraktor. |
| `EngineSession` | Opaques Handle, Rollen-/Signaturbindung, Token-Hash, Sequenzzähler und TTL. |
| `DIRECT_INGEST_AUTH_REQUIRED_OPS` | Liste aller Operationen, die Engine-Session-Binding benötigen. |
| `enforce_zero_logic_gateway()` | PHP-seitige Transport-Sperre gegen Klartext-POSTs. |
| `direct-ingest.js` | Versiegelt Formularnutzlast und Request-Token gemeinsam im Browser. |

### 18.6 Neue Tests

Die Testsuite wurde um `tests/test_zero_logic_session_binding.py` erweitert. Sie prüft:

1. Eine Mutation ohne versiegeltes Request-Token wird abgelehnt.
2. Eine Mutation mit gültigem Engine-Session-Handle und versiegeltem Request-Token wird akzeptiert.
3. Das Request-Token rotiert nach erfolgreicher Mutation.
4. Ein altes Request-Token kann danach nicht erneut verwendet werden.
5. PHP ist nicht die Quelle der Autorität; die Engine injiziert die gültige Identität.

Der aktuelle Teststand für Projektversion 1.9:

```text
Ran 17 tests in 4.160s

OK
```

### 18.7 Sicherheitseinordnung

Projektstand 1.9 verbessert die PHP-Sicherheitslage strukturell. PHP ist im Normalbetrieb kein Klartext-Interpreter für Formular- oder Contentdaten mehr, sondern ein Zero-Logic-Gateway für versiegelte Mutationen, Sessions und statische Auslieferung. Risiken bleiben bei Tokenbindung, Gateway-Allowlists, Fehlkonfiguration, Upload-Grenzen und dem bewusst autorisierten DSGVO-Export. Der Sicherheitsgewinn besteht darin, dass PHP keine Berechtigungsentscheidung mehr treffen und keine Klartextformularinhalte mehr semantisch interpretieren muss.

Für den strengen VRAM-only-Anspruch bleibt weiterhin offen:

- Python öffnet den Direct-Ingest-Envelope noch im CPU-RAM.
- Snapshot-Restore materialisiert aktuell weiterhin Python-Objekte.
- Normale PHP-Mutationspfade erhalten keine Formular-Klartexte. Falls ein Read- oder Exportpfad sichtbare Daten ausgibt, muss er als autorisierte Ausgabe und nicht als Direct-Ingest-Mutation bewertet werden; der besonders sensible Ausnahmefall ist der DSGVO-Export „Eigene Daten herunterladen“.
- Ein externer Memory-Probe muss weiterhin negative Befunde während Login, Mutation, Query und Restore liefern.

Die korrekte Einordnung lautet daher:

> MyceliaDB v1.9 erreicht ein PHP-blindes, Engine-autorisiertes Webprotokoll mit rotierenden Engine-Request-Tokens. Es reduziert PHP-spezifische Angriffsklassen erheblich, beweist aber noch nicht vollständige CPU-RAM-freie VRAM-Residency.

---

## 19. Projektstand 1.10: Native-GPU-Envelope-Opening und Strict-VRAM-Zertifizierungs-Gate

Projektstand 1.10 führt den entscheidenden Beweisrahmen für die stärkste Sicherheitsbehauptung ein: Der Anspruch auf „Strict-VRAM-Sicherheit“ darf erst dann als belastbar gelten, wenn Direct-Ingest-Envelope-Opening, Snapshot-Restore und externe Memory-Forensics gemeinsam belegen, dass sensible Klartextfragmente nicht im CPU-RAM erscheinen.

Wichtig ist die Trennung zwischen Implementierung und Zertifizierung:

- **Implementiert ist jetzt der Enterprise-Vertrag**, der eine native GPU-Residency-Schicht laden, prüfen, selbsttesten und in die Zertifizierungsentscheidung einbeziehen kann.
- **Nicht vorgetäuscht wird eine falsche Zertifizierung**, wenn die native Bibliothek oder ihre Exporte fehlen. In diesem Fall bleibt die Strict-VRAM-Zertifizierung fail-closed blockiert.

### 19.1 Native GPU Residency Bridge

Neu ist die `NativeGPUResidencyBridge` in `html/mycelia_platform.py`. Sie sucht optional nach einer nativen Bibliothek, die Direct-Ingest-Envelope-Opening und Snapshot-Restore direkt in GPU-eigene Speicherbereiche ausführen kann.

Die Suchreihenfolge umfasst unter anderem:

```text
MYCELIA_GPU_ENVELOPE_LIBRARY
html/
Projektwurzel/
Mycelia_Database-main/
Mycelia_Database-main/build/
```

Der erwartete native Contract besteht aus folgenden Exporten:

| Export | Rolle |
|---|---|
| `mycelia_gpu_envelope_capabilities_v1` | Liefert maschinenlesbare Fähigkeiten der nativen Residency-Schicht. |
| `mycelia_gpu_residency_selftest_v1` | Führt einen nativen Residency-Selbsttest aus. |
| `mycelia_gpu_envelope_open_to_vram_v1` | Öffnet Direct-Ingest-Envelope ohne Rückgabe des Klartext-Payloads an Python. |
| `mycelia_gpu_snapshot_restore_to_vram_v1` | Stellt Snapshots direkt in GPU-residente Strukturen wieder her. |

Damit ist die Schnittstelle vorbereitet, an der ein echter C/C++/OpenCL- oder Rust-Native-Opener angebunden werden kann. Solange diese Funktionen nicht vorhanden sind, bleibt der Modus ehrlich bei Phase 1: PHP-blind, aber Python-materialisiert.

### 19.2 Neue Engine-Befehle

Projektstand 1.10 ergänzt folgende Befehle:

| Befehl | Zweck |
|---|---|
| `native_gpu_capability_report` | Meldet, ob die native GPU-Residency-Bibliothek geladen wurde und welche Exporte verfügbar sind. |
| `native_gpu_residency_selftest` | Startet den nativen Selftest, sofern die Bibliothek verfügbar ist. |
| `strict_vram_certification` | Kombiniert native Fähigkeiten, Selftest, externe Memory-Probe und Runtime-Status zu einer finalen Zertifizierungsentscheidung. |

Die Zertifizierung ist absichtlich fail-closed. Ein fehlender nativer Export, ein fehlender externer RAM-Probe oder ein CPU-materialisierter Restore blockiert die Hardware-Residency-Behauptung.

### 19.3 Zertifizierungslogik

`strict_vram_certification` meldet nur dann einen bestandenen Strict-VRAM-Gate, wenn alle Bedingungen erfüllt sind:

1. `MYCELIA_STRICT_VRAM_CERTIFICATION=1` ist aktiv.
2. OpenCL/GPU-Crypto ist aktiv.
3. Native Direct-Ingest-Envelope-Öffnung in VRAM ist verfügbar.
4. Native Snapshot-Wiederherstellung in VRAM ist verfügbar.
5. Der native Residency-Selftest wurde bestanden.
6. Der letzte Restore wurde nicht im Python-CPU-RAM materialisiert.
7. Ein negativer externer CPU-RAM-Probe für genau diese MyceliaDB-PID wurde eingereicht.
8. Snapshot- und Graph-Scans zeigen keine Klartexttreffer.

Das ist der relevante Unterschied zu früheren Versionen: Der Beweis ist nicht mehr eine Formulierung im Whitepaper, sondern ein maschinenlesbares Gate.

### 19.4 Neues Audit-Werkzeug

Neu ist:

```text
tools/mycelia_strict_vram_certify.py
```

Dieses Werkzeug orchestriert die Zertifizierung gegen die laufende Engine:

```powershell
python tools\mycelia_strict_vram_certify.py --engine http://127.0.0.1:9999 --json-out strict_cert.json
```

Mit vorhandenem externen Memory-Probe-Report:

```powershell
python tools\mycelia_strict_vram_certify.py --engine http://127.0.0.1:9999 --probe-report residency_probe.json --json-out strict_cert.json
```

Der Exit-Code ist `0`, wenn die strenge Zertifizierung besteht, und `2`, wenn sie nicht besteht. Dadurch kann der Audit in CI/CD oder Deployment-Freigaben eingebunden werden.

### 19.5 Admin-Konsole

Die Admin-Konsole enthält jetzt zusätzliche Aktionen:

- Native-GPU-Opener prüfen
- Native-GPU-Selftest ausführen
- Strict-VRAM-Zertifizierung ausführen

Dadurch kann der Betreiber direkt im Webinterface sehen, welche Beweisstücke fehlen. Typische Blocker sind:

```text
Native GPU envelope/snapshot opener library is not available.
Direct-Ingest envelopes are not opened directly into VRAM.
Snapshots are not restored directly into VRAM.
Native residency self-test has not passed.
No negative external CPU-RAM memory probe has been submitted for the current MyceliaDB PID.
```

### 19.6 Enterprise-Testabdeckung

Neu ist:

```text
tests/test_native_gpu_residency_contract.py
```

Die Tests prüfen:

1. Das System zertifiziert nicht falsch, wenn native Exporte fehlen.
2. Eine negative externe Memory-Probe allein reicht nicht aus.
3. Die strenge Hardware-Residency-Behauptung bleibt blockiert, solange native Envelope- und Snapshot-Opener fehlen.

Aktueller Teststand für Projektversion 1.10:

```text
Ran 19 tests in 3.309s

OK
```

### 19.7 Sicherheitsbewertung

Projektstand 1.10 ist ein wichtiger Schritt, weil er die stärkste Aussage nicht mehr als Marketingbehauptung behandelt. Die Plattform kann jetzt ausdrücklich zwischen folgenden Zuständen unterscheiden:

| Zustand | Bedeutung |
|---|---|
| PHP-blind Direct Ingest | PHP sieht keine Formular-Klartexte. |
| Python-materialisierter Direct Ingest | Python öffnet den Envelope noch im CPU-RAM. |
| Native-GPU-Envelope-Opening | Envelope wird nativ geöffnet und soll nicht als Python-Objekt erscheinen. |
| GPU-Snapshot-Restore | Snapshot wird ohne Python-Klartextobjekte in GPU-Strukturen geladen. |
| Externer negativer RAM-Probe | Ein separater Prozess fand keine bekannten Klartextfragmente im CPU-RAM. |
| Strict-VRAM-Zertifizierung | Alle Bedingungen wurden gemeinsam erfüllt. |

Die korrekte Einordnung lautet:

> MyceliaDB v1.10 implementiert den Enterprise-Beweisrahmen für die strenge VRAM-Residency. Solange keine native GPU-Residency-Bibliothek mit den geforderten Exporten vorhanden ist, bleibt die Plattform bewusst nicht zertifiziert. Sobald diese Bibliothek angebunden ist und externe Memory-Forensics negativ ausfallen, kann die Hardware-Residency-Sicherheitsbehauptung erstmals maschinenlesbar und reproduzierbar geprüft werden.



---

## Nachtrag v1.11: Session-Token-Drift und Strict-VRAM-Only-Fail-Closed

Der beobachtete Fehler beim Wechsel von Profil zu Forum/Blog war kein Hinweis auf
einen defekten Autosnapshot. Die Ursache lag in der Protokollbindung der
flüchtigen Engine-Session: session-bound Read-Operationen rotierten den
Request-Token in der Engine, gaben den neuen Token aber nicht an PHP zurück. Das
nächste Direct-Ingest-Manifest verwendete dadurch einen veralteten Token und die
Engine blockierte korrekt mit „Request-Token passt nicht zum flüchtigen
Engine-Attraktor“.

v1.11 korrigiert diese Protokollstelle. Jede session-bound Read- oder
Mutation-Operation, die den Token rotiert, liefert nun das neue
`engine_session`-Objekt an PHP zurück. PHP bleibt weiterhin Zero-Logic-Gateway,
übernimmt aber das opaque Session-Material, ohne Autoritätsentscheidungen zu
treffen.

Zusätzlich wurde `MYCELIA_STRICT_VRAM_ONLY=1` eingeführt. In diesem Modus
arbeitet MyceliaDB fail-closed: Direct-Ingest-Envelopes und Snapshots werden
nicht mehr in Python geöffnet, solange keine native GPU-Envelope- und
GPU-Snapshot-Restore-Bibliothek verfügbar ist. Dadurch wird verhindert, dass
Phase-1-Python-Materialisierung fälschlich als strenge VRAM-only-Residency
interpretiert wird.


---

## 20. Projektstand 1.12: Enterprise Session Token Broker gegen Token-Drift

Nach der Einführung des Zero-Logic-Gateways wurde ein praktischer Navigationsfehler sichtbar: Beim Wechsel zwischen Profil, Forum und Blog rotierten session-gebundene Read-Calls den flüchtigen Engine-Request-Token. Dadurch konnten Formulare, die mit einem veralteten Browser-Manifest versiegelt wurden, korrekt aber für den Nutzer störend mit `Request-Token passt nicht zum flüchtigen Engine-Attraktor` abgelehnt werden.

Projektstand 1.12 führt deshalb einen Engine-seitigen **One-Time-Token-Pool** ein:

1. `direct_ingest_manifest` ist jetzt selbst session-gebunden.
2. Jeder Manifest-Abruf erzeugt einen frischen, kurzlebigen Formular-Token.
3. Der Formular-Token wird browserseitig im WebCrypto-Envelope versiegelt.
4. PHP leitet weiterhin nur `sealed_ingest` und `direct_op` weiter.
5. Die Engine konsumiert den Formular-Token einmalig und rotiert danach den Session-Attraktor.
6. Bereits konsumierte Tokens können nicht wiederverwendet werden.
7. Normale Seitenwechsel, Read-Calls und mehrere Formulare zerstören sich nicht mehr gegenseitig.

Zusätzlich wurde ein kritischer Signaturkonflikt behoben: Engine-Autorität liefert die Nutzeridentität als `actor_signature`, darf aber Zielsignaturen wie Forum-Thread-, Kommentar-, Blog- oder Blogpost-Signaturen nicht überschreiben. Dadurch funktionieren Update-, Delete-, Comment- und Reaction-Aktionen wieder korrekt unter Zero-Logic-Bedingungen.

### 20.1 Geprüfte Web-Aktionen

Die neue Regression-Suite simuliert die vollständige PHP-Navigation und alle mutierenden Web-Aktionen:

- Profil lesen und aktualisieren
- Forum listen
- Forenbeitrag erstellen
- Forenbeitrag lesen, ändern und löschen
- Kommentare erstellen und löschen
- Likes und Dislikes setzen
- Blogs listen, erstellen, ändern und löschen
- Blogposts erstellen, lesen, ändern und löschen
- Blogpost-Kommentare und Reaktionen
- Manifest-Token als One-Time-Token
- Replay eines bereits verwendeten Tokens wird abgelehnt

Testdatei:

```text
tests/test_web_action_token_integrity.py
```

Der Sicherheitszustand bleibt unverändert konservativ: PHP ist weiterhin Zero-Logic-Gateway, aber strenge VRAM-only-Residency wird erst durch native GPU-Envelope-Öffnung, GPU-Snapshot-Restore und negative externe Memory-Probes zertifizierbar.


---

## Projektstand 1.13: Admin-CMS und Engine-basierte Rechteverwaltung

Mit Version 1.13 wurde die Weboberfläche um ein echtes Enterprise-Admin-Panel erweitert. Ziel ist nicht nur Moderation von Forum und Blog, sondern zentrale Steuerung aller angezeigten Webseitentexte und aller Benutzerrechte über MyceliaDB.

### Admin-CMS für Webseitentexte

Alle editierbaren UI-Texte werden in `www/site_texts.php` als stabiler Schlüssel-Katalog registriert. Die sichtbaren Texte werden zur Laufzeit über `txt(key)` aufgelöst. Änderungen aus dem Admin-Panel werden nicht in PHP-Dateien geschrieben, sondern als verschlüsselte Mycelia-Attraktoren in der Tabelle `mycelia_site_texts` gespeichert und über Autosnapshot persistiert.

Neue Engine-Befehle:

- `list_site_texts`
- `admin_set_site_text`

Damit ist PHP weiterhin nur Darstellungs- und Transportebene. Die Engine autorisiert die Änderung über `admin.texts.manage`, speichert den Text verschlüsselt und liefert Safe-Fragments bzw. gecachte Overrides an das Frontend.

### Benutzerrechte und Rechteentzug

Benutzerprofile enthalten jetzt zusätzlich ein versionierbares Rechtefeld `permissions`. Rollen und Rechte werden bei jeder Engine-Session-Validierung aus dem User-Attraktor neu geladen. Dadurch werden Rechteänderungen sofort wirksam, auch ohne erneuten Login.

Neue Engine-Befehle:

- `list_users`
- `permission_catalog`
- `admin_update_user_rights`

Der Rechtekatalog umfasst unter anderem:

- `profile.update`
- `forum.create`
- `forum.comment`
- `forum.react`
- `blog.create`
- `blog.post.create`
- `blog.comment`
- `blog.react`
- `content.moderate`
- `admin.access`
- `admin.users.manage`
- `admin.texts.manage`

Alle mutierenden Admin-Aktionen laufen weiterhin über Direct GPU Ingest. PHP liest keine Klartextfelder aus den Admin-Formularen aus, sondern leitet nur versiegelte Pakete an die Engine weiter. Mehrfachwerte wie Checkbox-Rechte werden browserseitig korrekt als Array versiegelt.

### Sicherheitsrelevante Korrektur

Die Session-Autorität der Engine überschreibt keine Zielparameter mehr wie `signature`, `role` oder `permissions`. Das verhindert, dass bei Admin-Aktionen versehentlich die Actor-Rolle anstelle der Zielrolle gespeichert wird. Actor-Daten bleiben ausschließlich unter `actor_*` verfügbar.

### Tests

Neu ergänzt wurde:

```text
tests/test_admin_cms_rights.py
```

Die Tests prüfen:

1. Admin kann Webseitentexte ändern.
2. Textänderungen werden im Snapshot verschlüsselt gespeichert.
3. Nach Restore sind die CMS-Texte wieder verfügbar.
4. Admin kann `forum.create` entziehen.
5. Der Rechteentzug wirkt auf eine bereits aktive User-Session ohne Re-Login.
6. Ein User ohne `forum.create` kann keine Forenbeiträge mehr erstellen.

Teststand:

```text
Ran 25 tests

OK
```



---

## 18. Projektstand 1.14: Datenschutz-Center, Datenexport und Account-Löschung

MyceliaDB Enterprise v1.14 ergänzt die Plattform um Betroffenenrechte-Funktionen für angemeldete Nutzer. Grundlage sind insbesondere das Auskunftsrecht, das Recht auf Löschung und die Datenübertragbarkeit. Die Implementierung ist technisch so gestaltet, dass PHP weiterhin keine Autoritätsentscheidung trifft: Berechtigung, Passwortbestätigung, Exportumfang und Löschkaskade werden durch die Mycelia-Engine geprüft.

### 18.1 Neue Weboberfläche

Im Ordner `www/` wurden ergänzt:

- `privacy.php`: Datenschutz-Center für angemeldete Nutzer.
- `download_my_data.php`: session-gebundener JSON-Export.
- Navigationspunkt `Datenschutz`.
- Profil-Aktion `Datenschutz & Datenexport`.

Der Export erzeugt ein strukturiertes, maschinenlesbares JSON im Format `MYCELIA_SUBJECT_EXPORT_V1`. Enthalten sind Profilwerte, eigene Forenbeiträge, Kommentare, Reaktionen, eigene Blogs und Blogposts. Credential-äquivalente Geheimnisse wie Passwort oder `auth_pattern` werden bewusst nicht exportiert.

### 18.2 Neue Engine-Befehle

| Befehl | Zweck | Sicherheitsmodell |
|---|---|---|
| `export_my_data` | Erzeugt ein personenbezogenes JSON-Paket für den eingeloggten Nutzer | Session-bound Read, Engine autorisiert den Actor |
| `delete_my_account` | Löscht User-Attraktor und zugeordnete personenbezogene Inhaltsknoten | Direct-Ingest, One-Time-Token, Passwortbestätigung, Engine-Autorität |

### 18.3 Löschmodell

`delete_my_account` führt eine harte Entfernung aus dem aktiven DAD-Graphen durch:

1. User-Attraktor wird entfernt.
2. Eigene Forenbeiträge werden entfernt.
3. Eigene Kommentare werden entfernt.
4. Eigene Reaktionen werden entfernt.
5. Eigene Blogs werden entfernt.
6. Eigene Blogposts sowie Posts in eigenen Blogs werden entfernt.
7. Kommentare und Reaktionen auf gelöschte Inhalte werden kaskadiert entfernt, um verwaiste Referenzen zu vermeiden.
8. Nicht-eigene Referenzen wie CMS-Update-Marker werden auf `erased-user` gescrubbt.
9. Alle aktiven Engine-Sessions des Accounts werden widerrufen.
10. Der Autosnapshot wird neu geschrieben, damit gelöschte Knoten nach Neustart nicht wiederhergestellt werden.

### 18.4 Residency-Einordnung

Der Datenexport ist ein absichtlicher Offenlegungs-Endpunkt. Er muss personenbezogene Daten für den authentifizierten Nutzer materialisieren, damit der Browser eine Datei herunterladen kann. Deshalb ist der Export kein VRAM-only-Pfad. Für den normalen Plattformbetrieb bleiben Direct-Ingest, Session-Binding und Snapshot-Verschlüsselung erhalten.

### 18.5 Neue Tests

Ergänzt wurde:

```text
tests/test_privacy_rights.py
```

Der Test prüft:

- Registrierung und Login.
- Erzeugung eigener Foren-, Kommentar-, Reaktions-, Blog- und Blogpost-Daten.
- Vollständigen JSON-Export der eigenen Daten.
- Ausschluss von Passwort/Auth-Pattern aus dem Export.
- Account-Löschung mit `DELETE`-Bestätigung und Passwortprüfung.
- Entfernung des User-Attraktors.
- Entfernung eigener Inhalte.
- Fehlschlag eines Logins nach Löschung.
- Token-Stabilität auch bei semantisch abgelehnten Löschversuchen.

Teststand für v1.14:

```text
Ran 27 tests

OK
```


---

## Projektstand v1.18D: Native Snapshot Runtime und Persistenzmutation

v1.18D ergänzt die bisherige Native-Boundary-Kette um Snapshot-Runtime und native Persistenzmutation. Damit existiert nun eine native Schnittstelle für:

- `native_snapshot_autosave`
- `native_snapshot_restore`
- `native_snapshot_commit`
- `native_persist_mutation`
- `native_persist_delete`
- `native_persist_compact`

Neue native Exports:

```text
mycelia_gpu_snapshot_runtime_capabilities_v1
mycelia_gpu_persist_mutation_v1
mycelia_gpu_snapshot_commit_v1
```

Der erwartete Capability-Report enthält:

```json
{
  "audit_version": "VRAM_RESIDENCY_AUDIT_V9_NATIVE_SNAPSHOT_RUNTIME",
  "native_snapshot_runtime_active": true,
  "native_persistence_mutation_active": true,
  "native_sensitive_command_executor": "partial-auth-content-admin-plugin-gdpr-snapshot-persistence",
  "strict_native_prerequisites_met": false
}
```

Die Sicherheitsgrenze bleibt bewusst konservativ. v1.18D akzeptiert Opaque-Handles für Snapshot- und Persistenzoperationen und gibt keine Graph-Payloads, keine Snapshot-Payloads, keine Mutationsdeskriptoren und keine Klartextdaten an Python zurück. Die Implementierung meldet aber weiterhin `envelope_to_vram=false`, `snapshot_to_vram=false` und `selftest_passed=false`, solange keine echte GPU-residente Entschlüsselung und kein vollständiger nativer Mycelia-Runtime-Port vorliegen.

Damit ist v1.18D die letzte Boundary-Stufe vor der externen Zertifizierung. Die nächste Stufe ist v1.18E: OS-Level-Memory-Probe, Driver-Residency-Attestation und Strict-VRAM-Zertifizierungs-Gate.


---

## Projektstand v1.18E: Strict Certification Gate und externer RAM-Probe

v1.18E ergänzt die bisherige native Boundary-Kette um die finale Zertifizierungslogik für die Strict-VRAM-These. Neu sind zwei native Exports:

```text
mycelia_gpu_strict_residency_evidence_v1
mycelia_gpu_external_probe_contract_v1
```

Die Engine kann damit unterscheiden zwischen:

1. vorhandener nativer Boundary,
2. behaupteter GPU-Residency,
3. nachgewiesener GPU-Residency,
4. externer CPU-RAM-Negativprüfung.

### Neue Report-Felder

```json
{
  "audit_version": "VRAM_RESIDENCY_AUDIT_V10_NATIVE_STRICT_CERTIFICATION_GATE",
  "native_strict_certification_gate_active": true,
  "external_ram_probe_contract_active": true,
  "gpu_resident_open_restore_proven": false,
  "strict_native_prerequisites_met": false
}
```

### Fail-Closed statt falscher Zertifizierung

Die Referenzbibliothek bleibt bewusst fail-closed:

```json
{
  "envelope_to_vram": false,
  "snapshot_to_vram": false,
  "selftest_passed": false,
  "gpu_resident_open_restore_proven": false
}
```

Das ist kein Rückschritt. v1.18E implementiert den Beweisrahmen und verhindert falsche Sicherheitsbehauptungen. Erst wenn eine produktive GPU-Open/Restore-Bibliothek diese Werte hardwaregestützt auf true setzt und ein negativer externer RAM-Probe für den laufenden PID vorliegt, darf die Strict-VRAM-Zertifizierung als bestanden gelten.

### Externer RAM-Probe

Neu ist ein Windows-Orchestrator:

```text
tools/run_v18e_external_ram_probe.ps1
```

Er sucht den laufenden `mycelia_platform.py`-Prozess, führt `mycelia_memory_probe.py` gegen dessen PID aus und ruft anschließend `mycelia_strict_vram_certify.py` mit dem Probe-Report auf. Damit ist die externe Memory-Forensics-Stufe reproduzierbar.


---

## Projektstand v1.18F: OpenCL-backed GPU-resident Open/Restore

v1.18F ersetzt die bisherige fail-closed Strict-Gate-Referenzschicht durch eine native OpenCL-Implementierung für `mycelia_gpu_envelope_open_to_vram_v1` und `mycelia_gpu_snapshot_restore_to_vram_v1`.

Die native DLL lädt OpenCL dynamisch, erstellt einen GPU-Kontext, legt die sealed Envelope-/Snapshot-Bytes als `cl_mem`-Buffer im GPU-Speicher ab und führt einen Digest-Kernel über diesen Buffer aus. Python erhält nur Opaque-Handles und Digest-Evidence, niemals Payload-, Profil-, Formular- oder Graph-Klartext.

Der neue native Vertrag lautet:

```json
{
  "contract": "MYCELIA_NATIVE_VRAM_OPEN_RESTORE_V1_18F",
  "envelope_to_vram": true,
  "snapshot_to_vram": true,
  "selftest_passed": true,
  "gpu_resident_open_restore_proven": true,
  "strict_evidence_mode": "opencl_vram_buffer_digest"
}
```

Diese Werte werden nur dann true, wenn OpenCL verfügbar ist, ein GPU-Gerät gefunden wird, der Kernel kompiliert und der VRAM-Digest-Selftest erfolgreich ausgeführt wurde. Andernfalls fällt die DLL geschlossen zurück und meldet den Grund.

### Sicherheitsgrenze

v1.18F beweist eine operative GPU-residente Native-Open/Restore-Strecke für sealed Bytes und Digest-only Evidence. Es ist jedoch keine vendor-signierte Hardware-Attestation. Eine Strict-VRAM-Aussage bleibt weiterhin nur dann zulässig, wenn zusätzlich der externe RAM-Probe für den laufenden Prozess negativ ist und der Plattformreport keine CPU-materialisierte Restore-/Payload-Strecke meldet.

### Build-Härtung

`html/native/build_native_gpu_envelope.ps1` wurde gehärtet:

- bevorzugt `vcvars64.bat`,
- baut mit `/MT`,
- linkt `/MACHINE:X64`,
- prüft die PE-Machine-ID `0x8664`,
- verhindert erneut `WinError 193` durch x86-DLLs.


---

## Projektstand 1.19: Mycelia Plugin Attractor System

Version 1.19 ergänzt ein Plugin-System, das bewusst nicht dem WordPress-Modell folgt. Es importiert keinen PHP-, Python-, Shell- oder JavaScript-Code als serverseitige Erweiterung. Plugins sind **deklarative Attraktor-Manifeste** mit einem festen Capability-Vertrag.

### Sicherheitsmodell

Ein Plugin besteht aus:

- `plugin_id`
- Name, Version, Beschreibung
- erlaubten Hooks
- erlaubten Capabilities
- Constraints, zum Beispiel `max_records` und `tension_threshold`
- Output-Schema

Explizit nicht erlaubt sind:

- PHP-Code
- Python-Code
- Shell-Code
- SQL
- Netzwerkzugriff
- Dateisystemzugriff
- Webhooks
- freie Graph-Scans
- Rohdatenrückgabe

Die Engine prüft Manifest-Schlüssel rekursiv. Verbotene Schlüssel wie `code`, `python`, `php`, `shell`, `socket`, `network`, `file`, `sql`, `eval`, `exec` oder `webhook` führen zur Ablehnung des Plugins.

### Neue Engine-Tabellen

| Tabelle | Zweck |
|---|---|
| `mycelia_plugins` | Speichert Plugin-Attraktoren mit verschlüsseltem Manifest |
| `mycelia_plugin_audit` | Speichert sichere Audit-Events zu Plugin-Ausführungen |

### Neue Engine-Befehle

| Befehl | Zweck |
|---|---|
| `plugin_catalog` | Liefert erlaubte Capabilities und Hooks |
| `list_plugins` | Listet installierte Plugin-Attraktoren |
| `admin_install_plugin` | Installiert oder aktualisiert ein deklaratives Plugin-Manifest |
| `admin_set_plugin_state` | Aktiviert oder deaktiviert ein Plugin |
| `admin_delete_plugin` | Entfernt einen Plugin-Attraktor |
| `run_plugin` | Führt ein Plugin in der Capability-Sandbox aus |

### Aktuell unterstützte Capabilities

- `stats.user.count`
- `stats.forum.count`
- `stats.blog.count`
- `stats.blog_post.count`
- `stats.comment.count`
- `stats.reaction.count`
- `stats.content.activity`

Diese Capabilities liefern ausschließlich Aggregate. Sie geben keine User-E-Mails, Profilfelder, Forenbeiträge, Kommentare oder Rohdatensätze zurück.

### Observer-Tension

Jede Plugin-Ausführung erzeugt einen deterministischen Tension-Wert. Er steigt bei vielen Capabilities oder unerlaubten Capabilities. Wird der Threshold überschritten, setzt die Engine das Plugin auf `suspended`, schreibt ein Audit-Event und verweigert die Ausgabe.

### Weboberfläche

Neu ist:

```text
www/plugins.php
```

Das Admin-Panel bietet:

- Manifest installieren
- Capability-Katalog anzeigen
- Plugins aktivieren/deaktivieren
- Plugins ausführen
- Plugins löschen
- letztes Safe-Result anzeigen

Alle Plugin-Mutationen laufen über Direct GPU Ingest. PHP interpretiert keine Plugin-Logik und führt keinen Plugin-Code aus.

### Tests

Neu ergänzt wurde:

```text
tests/test_plugin_attractor_system.py
```

Die Tests prüfen:

1. Admin kann ein sicheres Plugin installieren.
2. Plugin startet deaktiviert.
3. Admin kann es aktivieren.
4. `run_plugin` liefert nur Safe-Aggregate.
5. Rohdaten aus Forenbeiträgen leaken nicht in Plugin-Ausgaben.
6. Manifeste mit `code`-Schlüssel werden abgelehnt.
7. Normale User können keine Plugins installieren.
8. Das verschlüsselte Manifest leakt seine Beschreibung nicht im Snapshot.
9. Plugin kann gelöscht werden.

Teststand:

```text
Ran 40 tests

OK
```


---

## Nachtrag v1.19.1: Plugin-ID Normalisierung

Beim praktischen Test des Plugin-Systems wurde sichtbar, dass Admins häufig
menschenlesbare IDs oder alternative Manifest-Felder verwenden. Die Engine lehnte
solche Manifeste mit „Plugin-ID ungültig“ ab, obwohl dies kein sicherheitskritischer
Fehler war.

v1.19.1 normalisiert Plugin-IDs jetzt aus `plugin_id`, `id`, `pluginId`,
`plugin-id` oder ersatzweise aus `name`. Leerzeichen und Umlaute werden in eine
strikte interne ID überführt. Beispiel:

```text
Anonyme Statistiken 2026 -> anonyme_statistiken_2026
Öffentliche Übersicht -> oeffentliche_uebersicht
```

Die Sicherheitsgrenze bleibt unverändert: Das Plugin bleibt ein deklarativer
Attraktor ohne PHP/Python-Codeausführung, ohne Netzwerk, ohne Dateisystem und
ohne Rohdatenzugriff.


---

## v1.19.2 DLL Recognition Hotfix

Die Native-GPU-Residency-Bibliothek wird wieder automatisch unter
`html/native/mycelia_gpu_envelope.dll` erkannt. Die Native Residency Bridge wird
aktiv angefordert, sobald die DLL vorhanden ist; ein explizites Setzen von
`MYCELIA_NATIVE_GPU_ENVELOPE_OPENER=1` ist für die Erkennung nicht mehr nötig.

Wichtig: `CC_OpenCl.dll` und `mycelia_gpu_envelope.dll` sind unterschiedliche
ABIs. Die Core-OpenCL-DLL wird für den allgemeinen OpenCLDriver gesucht, während
`mycelia_gpu_envelope.dll` ausschließlich für den Native-GPU-Envelope-/VRAM-
Residency-Contract geladen wird.


---

## Projektstand 1.19.3: GPU-Crypto-Reporting

In früheren Reports konnte folgender scheinbar widersprüchlicher Zustand auftreten:

```json
{
  "opencl_active": true,
  "gpu_crypto_active": false,
  "native_gpu_envelope_opener": true,
  "gpu_restore_opener": true
}
```

Die Ursache war kein Hardwarefehler, sondern eine zu enge Definition des Feldes
`gpu_crypto_active`. Es prüfte nur den alten Core-/ChatEngine-Kryptopfad über
`driver_mode` und ignorierte den neuen nativen VRAM-Envelope-Pfad über
`mycelia_gpu_envelope.dll`.

Ab v1.19.3 ist das Reporting getrennt und zugleich zusammengeführt:

```json
{
  "core_gpu_crypto_active": false,
  "native_envelope_crypto_active": true,
  "gpu_crypto_active": true
}
```

Damit bleibt die Diagnose präzise:

- `core_gpu_crypto_active` steht für den alten `CC_OpenCl.dll`-/ChatEngine-Pfad.
- `native_envelope_crypto_active` steht für den nativen Envelope-/Restore-Pfad.
- `gpu_crypto_active` ist die operatorfreundliche Gesamtantwort: mindestens ein GPU-Kryptopfad ist aktiv.

Die strenge VRAM-Zertifizierung bleibt weiterhin an die separaten Evidence-Gates
gebunden und wird durch diese Reporting-Korrektur nicht künstlich freigeschaltet.


---

## Hotfix v1.19.4: Snapshot-Pfad-Fallback und Native Restore Audit

Dieser Hotfix behebt einen Fehler im Restore-Pfad: leere oder ältere Restore-Requests verwendeten `snapshots/mycelia.snapshot`, obwohl die Plattform standardmäßig `snapshots/autosave.mycelia` schreibt. Fehlte die Legacy-Datei, konnte ein `FileNotFoundError` bis zum HTTP-Handler durchschlagen und einen 500-Fehler erzeugen.

Änderungen:

- `restore_snapshot` nutzt nun einen zentralen `_resolve_snapshot_path`.
- Fallback-Reihenfolge: expliziter Pfad, `self.snapshot_path`, `DEFAULT_SNAPSHOT_PATH`, `snapshots/autosave.mycelia`, `snapshots/mycelia.snapshot`.
- Fehlende Snapshots liefern kontrolliert `{status: "error", message: "Snapshot-Datei nicht gefunden."}` statt Traceback.
- `restore_snapshot_residency_audit` nutzt bei aktivem Native Snapshot Runtime den nativen Selftest/Evidence-Pfad und ruft nicht mehr automatisch den Python-Restore auf.
- Dadurch wird `last_restore_cpu_materialized` nicht mehr durch den Audit-Button auf `true` gesetzt, wenn native Restore-Evidence verfügbar ist.

Neue Regressionstests:

```text
tests/test_snapshot_path_fallback.py
```

Teststand:

```text
Ran 48 tests in 17.625s

OK (skipped=1)
```


---

## Projektstand 1.19.5: Admin-/Console-Parität für VRAM-Evidence

In v1.19.5 wurde die VRAM-Audit-Anzeige im Admin-Panel an den Konsolenworkflow angeglichen. Vorher wurden Manifest, Probe-Submission, Native-Report, Selftest und Strict-Zertifizierung als getrennte Session-Fragmente angezeigt. Dadurch konnte das Admin-Panel veraltete Resultate zeigen, obwohl die Konsole bereits einen negativen externen RAM-Probe eingereicht hatte.

Neu ist der Engine-Befehl:

```text
strict_vram_evidence_bundle
```

Er erzeugt in einem einzigen Request ein konsistentes Evidence-Bundle mit:

- aktuellem PID,
- aktuellem Driver-Mode,
- Native-GPU-Capability-Report,
- Native-GPU-Selftest,
- zuletzt eingereichtem externem Memory-Probe,
- negativer RAM-Probe-Bewertung,
- letztem Restore-Materialisierungsstatus,
- vollständiger Strict-VRAM-Zertifizierung.

Das Admin-Panel ruft dieses Bundle automatisch nach dem Einreichen eines `residency_probe.json`-Reports sowie nach Native-Selftest und Strict-Zertifizierung ab. Zusätzlich gibt es den Button **Konsole/UI synchronisieren**, der den aktuellen Engine-Zustand neu ausliest und alle VRAM-Audit-Anzeigen aus demselben Evidence-Bundle befüllt.

Wichtig: Falls `strict_vram_certification_enabled=false` gemeldet wird, ist die Engine ohne `MYCELIA_STRICT_VRAM_CERTIFICATION=1` gestartet. Das Admin-Panel zeigt diesen Zustand jetzt explizit an, statt ihn mit fehlender Native-Fähigkeit zu verwechseln. Diese Einstellung muss vor dem Start von `mycelia_platform.py` gesetzt werden und wird nicht aus PHP heraus geändert.


---

## v1.19.6 Zero-Logic Admin Control Allowlist

Im Admin-Panel existieren zwei Kategorien von POST-Requests:

1. **Direct-Ingest-Mutationen** mit Nutzer-, Plugin-, CMS-, Profil- oder Content-Nutzlast. Diese bleiben strikt browserseitig versiegelt.
2. **Audit-Control-POSTs** ohne sensible Nutzlast, die nur Engine-Statusbefehle auslösen, etwa `residency_audit_manifest`, `native_gpu_residency_selftest` oder `strict_vram_evidence_bundle`.

Der Fehler `Zero-Logic Gateway: Klartext-POSTs sind deaktiviert` entstand, weil `run_vram_evidence_bundle` im zentralen Gateway-Allowlist fehlte. Dadurch blockierte PHP den Admin-Button `Konsole/UI synchronisieren`, obwohl dieser keine schützenswerte Formularnutzlast transportiert.

v1.19.6 ergänzt die Allowlist um:

- `run_vram_evidence_bundle`
- `run_vram_audit`

Die Zero-Logic-Regel bleibt erhalten: produktive Mutationen und alle Nutzlasten laufen weiterhin ausschließlich über `sealed_ingest` und `direct_op`.

Regressionstest:

```text
tests/test_zero_logic_gateway_allowlist.py
```

Teststand:

```text
Ran 50 tests

OK (skipped=1)
```


---

## v1.19.7: Classified RAM-Probes und Strict-Response-Hardening

Die externe RAM-Forensik wurde erweitert, um zwischen sicherheitsrelevanten Klartextfunden und nicht-sensitiven Betriebsartefakten zu unterscheiden. 64-stellige Node-Signaturen werden jetzt automatisch als `public_identifier` klassifiziert. Solche Treffer werden weiterhin vollständig protokolliert, blockieren aber nicht mehr die Strict-Zertifizierung, sofern keine sensiblen Klartexttreffer vorhanden sind.

Neue Probe-Klassen:

| Klasse | Strict-relevant | Bedeutung |
|---|---:|---|
| `sensitive_cleartext` | Ja | allgemeine sensible Testwerte |
| `profile_cleartext` | Ja | Profilfelder wie Ort, Name, E-Mail |
| `content_body` | Ja | Forum-/Blog-/Kommentarinhalt |
| `credential_equivalent` | Ja | Passwort-/Token-nahe Werte |
| `public_identifier` | Nein | öffentliche Node-Signaturen/Handles |
| `audit_artifact` | Nein | Challenge-/Evidence-Artefakte |

Das Tool `tools/mycelia_memory_probe.py` erzeugt nun Reports im Format `MYCELIA_CPU_RAM_PROBE_V2_CLASSIFIED`. Es unterstützt zusätzlich:

```powershell
--probe-sensitive "SECRET"
--probe-public "4166bbf4..."
--probe-audit "challenge-id"
```

`--probe` bleibt kompatibel und klassifiziert automatisch: 64-hex-Werte als `public_identifier`, normale Strings als `sensitive_cleartext`.

Die Engine akzeptiert weiterhin alte V1-Reports, behandelt unklassifizierte Treffer aber fail-closed als sensitiv. Neue Felder im Evidence-Report:

- `probe_manifest`
- `hit_counts_by_kind`
- `strict_hits`
- `non_strict_hits`
- `strict_negative`
- `raw_negative`
- `classified_findings`

Zusätzlich wurde ein Strict-Response-Hardening eingeführt. Bei aktivem `MYCELIA_STRICT_VRAM_CERTIFICATION=1` und `MYCELIA_STRICT_RESPONSE_REDACTION=1` werden normale JSON-Response-Pfade für Profil-/Content-Daten redaktionell gehärtet. `get_profile` entschlüsselt Profilwerte in diesem Modus nicht mehr automatisch; Content-Felder in Responses werden durch Strict-Redaction-Marker ersetzt. Der autorisierte DSGVO-Export bleibt bewusst ein Offenlegungspfad und ist von dieser Redaction ausgenommen.

Professionelle Einordnung: Diese Änderung ersetzt keine native Vollausführung aller Commands, reduziert aber langlebige CPU-RAM-Response-Artefakte und macht die Zertifizierung präziser. Für ein grünes Strict-Gate müssen `strict_hits=0`, Native-VRAM-Evidence und ein passender externer Probe für die aktuelle PID vorliegen.


---

## Projektstand 1.19.9: Scheduled Heartbeat Audit

Version 1.19.9 automatisiert den zuvor manuell ausgeführten Strict-VRAM-Evidence-Lauf als signierten 24-Stunden-Heartbeat. Ziel ist ein laufender, reproduzierbarer Hardware-Residency-Status im Admin-Dashboard.

### Ziel

Der manuelle Audit-Prozess aus Kapitel 12 der Dokumentation wurde in einen externen Heartbeat-Prozess überführt:

1. Die Engine erzeugt ein `residency_audit_manifest` mit PID und Challenge-ID.
2. Ein externes Tool erzeugt ein frisches Random-Secret.
3. Das Random-Secret wird in einer temporären Probe-Datei an `mycelia_memory_probe.py` übergeben.
4. Der externe Scanner prüft den CPU-RAM des laufenden Engine-Prozesses.
5. Das Probe-Ergebnis wird an die Engine zurückgereicht.
6. Die Engine erzeugt ein `strict_vram_evidence_bundle`.
7. Das Heartbeat-Tool signiert den Evidence-Lauf mit Ed25519.
8. Die Engine verifiziert die Signatur und speichert nur die maschinenlesbare Evidence-Zusammenfassung.
9. Das Admin-Dashboard zeigt den aktuellen Status als `ZERTIFIZIERT`, `NICHT ZERTIFIZIERT` oder `ABGELAUFEN`.

### Neue Dateien

```text
tools/mycelia_heartbeat_audit.py
tools/run_heartbeat_audit.ps1
tools/install_heartbeat_audit_task.ps1
tests/test_scheduled_heartbeat_audit.py
```

### Neue Engine-Befehle

| Befehl | Zweck |
|---|---|
| `submit_heartbeat_audit` | Nimmt einen signierten Heartbeat-Evidence-Report entgegen und verifiziert ihn. |
| `heartbeat_audit_status` | Liefert den letzten signierten Heartbeat-Status für das Admin-Dashboard. |

Zusätzlich enthält `strict_vram_evidence_bundle` jetzt das Feld:

```json
{
  "scheduled_heartbeat_audit": {
    "certified": true,
    "state": "strict-certified",
    "display": {
      "label": "Aktueller Hardware-Residency-Status",
      "value": "ZERTIFIZIERT"
    }
  }
}
```

### Signaturmodell

Das Heartbeat-Tool nutzt Ed25519. Beim ersten Lauf werden lokale Audit-Schlüssel erzeugt:

```text
docs/audit_keys/heartbeat_ed25519_private.pem
docs/audit_keys/heartbeat_ed25519_public.pem
```

Die Engine vertraut standardmäßig dem öffentlichen Schlüssel:

```text
docs/audit_keys/heartbeat_ed25519_public.pem
```

Alternativ kann der Pfad explizit gesetzt werden:

```powershell
$env:MYCELIA_HEARTBEAT_PUBLIC_KEY="D:\web_sicherheit\docs\audit_keys\heartbeat_ed25519_public.pem"
```

Wichtig: Der private Schlüssel wird nicht mitgeliefert und darf nicht veröffentlicht werden.

### Manueller Heartbeat-Lauf

```powershell
cd D:\web_sicherheit
powershell -ExecutionPolicy Bypass -File .\tools\run_heartbeat_audit.ps1 -ProjectRoot D:\web_sicherheit -Engine http://127.0.0.1:9999/
```

### Scheduled Task installieren

```powershell
cd D:\web_sicherheit
powershell -ExecutionPolicy Bypass -File .\tools\install_heartbeat_audit_task.ps1 -ProjectRoot D:\web_sicherheit -Engine http://127.0.0.1:9999/ -At 03:15
```

Der Task führt einmal täglich den externen RAM-Probe aus, reicht das Ergebnis ein, signiert den Evidence-Lauf und aktualisiert den Dashboard-Status.

### Admin-Dashboard

Das Admin-Panel zeigt nun:

```text
Scheduled Heartbeat Audit
Aktueller Hardware-Residency-Status: ZERTIFIZIERT
```

Der Status gilt nur, solange der letzte Heartbeat jünger als `MYCELIA_HEARTBEAT_MAX_AGE_SECONDS` ist. Standardwert:

```text
93600 Sekunden = 26 Stunden
```

Damit erhält ein täglich geplanter 24-Stunden-Task zwei Stunden Toleranz.

### Sicherheitsgrenzen

Der Heartbeat beweist nicht allgemeine Unhackbarkeit. Er bestätigt für den jeweiligen Lauf:

- Native-VRAM-Pfade waren aktiv.
- Strict Gate war aktiv.
- Ein frisches Random-Secret wurde extern geprüft.
- Der externe CPU-RAM-Probe war strict-negativ.
- Der letzte Restore war nicht CPU-materialisiert.
- Die Evidence wurde signiert und von der Engine verifiziert.

Damit wird der projektinterne Strict-VRAM-Evidence-Gate nicht nur manuell, sondern kontinuierlich und dashboardfähig überprüfbar.



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

## Projektstand v1.19.11: PHP Safe-Rendering Phase 2

Nach der Aktivierung von Strict-VRAM-Response-Redaction liefern einige Engine-Endpunkte keine einfachen Strings mehr zurück, sondern strukturierte Safe-Fragments, zum Beispiel:

```json
{"text":"[redacted:strict-vram]"}
```

v1.19.10 hatte bereits die zentrale Escaping-Funktion `e()` gehärtet. In Forum-, Thread- und Blog-Detailseiten blieben jedoch zwei weitere PHP-Typgrenzen offen:

1. `layout_header(string $title)` akzeptierte noch ausschließlich Strings.
2. Hilfsfunktionen wie `ownership_actions()` und Routing-Hilfen erwarteten teilweise skalare Signaturen/Titel.

Wenn ein redigierter Engine-Wert als Array in `layout_header()` gelangte, entstand ein PHP-Fatal-Error:

```text
Fatal error: layout_header(): Argument #1 ($title) must be of type string, array given
```

### Änderung

Die Render-Schicht wurde vollständig auf `mixed`-sichere Eingaben umgestellt:

- `layout_header(mixed $title)`
- `ownership_actions(mixed $ownerSignature, mixed $editUrl, mixed $deleteName, mixed $signature)`
- neue Hilfsfunktion `mycelia_url_component(mixed $value)`
- neue Hilfsfunktion `mycelia_identity(mixed $value)`
- `fmt_time()` ignoriert strukturierte Redaction-Objekte kontrolliert
- Flash-Messages werden über `mycelia_scalar_text()` normalisiert

Damit gilt: Strukturierte Engine-Werte dürfen die UI nicht mehr mit `Array to string conversion` oder TypeErrors abbrechen. Sie werden entweder als Safe-Text, `[redacted:strict-vram]`, `[structured-data]` oder leere technische ID behandelt.

### Betroffene Seiten

Geprüft und gehärtet wurden insbesondere:

- `forum.php`
- `thread.php`
- `blogs.php`
- `blog.php`
- `my_blog.php`
- `admin.php`
- `privacy.php`
- `plugins.php`

### Tests

Der bestehende Safe-Rendering-Test wurde erweitert:

```text
tests/test_php_safe_rendering.py
```

Teststand:

```text
Ran 57 tests

OK (skipped=1)
```

PHP-Syntaxprüfung:

```text
www/*.php
No syntax errors detected
```


---

## Projektstand 1.19.12: Web-UI-Klartextanzeige bei weiterhin strengem Audit-Pfad

In v1.19.11 wurden Engine-Safe-Fragments korrekt gerendert, wodurch PHP-Warnungen und `array given`-Fatal-Errors beseitigt wurden. Dadurch wurden Forum-, Blog- und Profilinhalte im Strict-VRAM-Modus jedoch als `[redacted:strict-vram]` angezeigt. Das war sicherheitstechnisch korrekt, aber für die normale Webanwendung unbrauchbar.

v1.19.12 trennt deshalb zwei Betriebsarten sauber:

1. **Audit-/Evidence-Pfad**
   - Engine mit Strict-Schaltern starten,
   - externen Random-Secret-Probe ausführen,
   - `strict_vram_evidence_bundle` abrufen,
   - keine DSGVO-Exportfunktion während des Audits nutzen.

2. **Human-Web-UI-Pfad**
   - Forum, Blog, Profil und Admin-Mutationen laufen über PHP-blinden Direct Ingest,
   - PHP erhält `sealed_ingest` und `direct_op`, nicht die Formular-Klartexte,
   - PHP hält opaques Engine-Session-/Tokenmaterial,
   - die bewusste Klartextausnahme ist der DSGVO-Export „Eigene Daten herunterladen“.

Wichtig: Ein RAM-Probe darf nicht aus einem bewusst erzeugten Export- oder Anzeigezustand verallgemeinert werden. Für die Strict-VRAM-Evidence-Bewertung bleibt der dokumentierte Ablauf maßgeblich: Engine sauber starten, frischen Random-Secret-Probe ausführen, Evidence einreichen und Bundle prüfen.

### Neue/angepasste Schalter

| Schalter | Standard | Bedeutung |
|---|---:|---|
| `MYCELIA_WEB_UI_CLEAR_TEXT_RESPONSES` | `1` | Engine erlaubt definierte autorisierte Read-/Anzeigeantworten. Mutationen bleiben Direct-Ingest-versiegelt. |
| `MYCELIA_PHP_CLEAR_TEXT_UI` | historischer Schalter | In der aktuellen Sicherheitsbeschreibung nicht als PHP-Klartextmodell werten; PHP-Mutationen bleiben blind. Ausnahme: DSGVO-Export. |
| `MYCELIA_STRICT_RESPONSE_REDACTION` | abhängig von Strict | Redigiert normale Responses, sofern kein autorisierter UI-Read vorliegt. |

### Sicherheitsabgrenzung

Diese Änderung hebt den Strict-Evidence-Mechanismus nicht auf. Sie stellt sicher, dass die Webseite nutzbar bleibt, ohne PHP wieder zu einer Klartext-Mutationsschicht zu machen. Evidence-Status und Heartbeat-Audit dürfen weiterhin nicht aus einem DSGVO-Export oder einer Anzeigeausgabe abgeleitet werden, sondern aus dem externen Random-Secret-Audit.


---

## Projektstand 1.20: Enterprise-Sicherheits- und Skalierungsstufe

Version 1.20 erweitert MyceliaDB um sechs produktionsrelevante Enterprise-Fähigkeiten. Ziel ist nicht, das Strict-VRAM-Evidence-Gate zu ersetzen, sondern die Plattform um formale Abfragen, Nachvollziehbarkeit, Cluster-Fähigkeit und gehärtete Runtime-Grenzen zu ergänzen.

### 1. Semantic Mycelia Query Language (SMQL)

SMQL verbindet deterministische Filter mit semantischer Myzel-Rangfolge. Eine Abfrage wie:

```text
FIND mycelia_users WHERE role=admin ASSOCIATED WITH "High Security" LIMIT 10
```

wird intern in zwei Phasen übersetzt:

1. deterministischer Filter über `DynamicAssociativeDatabase.query_sql_like`,
2. semantisches Ranking über Cue-Vektor und `mood_vector`-Ähnlichkeit.

Neue Engine-Befehle:

```text
smql_explain
smql_query
```

Die Implementierung ist bewusst klein und auditierbar. Sie erlaubt `FIND`, `WHERE`, `AND`, `ASSOCIATED WITH` und `LIMIT`, aber keine freie Codeausführung.

### 2. Myzel-Föderation

Die Föderation ermöglicht den kontrollierten Austausch stabiler Attraktoren zwischen Engine-Instanzen. Sie schreibt keine Remote-Daten direkt in produktive Tabellen, sondern importiert sie als `mycelia_federated_influx`. Dadurch entsteht ein Nährstoff-Influx statt eines Split-Brain-Schreibkonflikts.

Neue Engine-Befehle:

```text
federation_status
federation_peer_add
federation_peer_remove
federation_export_stable
federation_import_influx
```

Zusätzlich wurde `tools/mycelia_federation_sync.py` als externer Export-Helfer ergänzt. Produktionsimporte bleiben an einen authentifizierten Admin-Kanal gebunden.

### 3. Cryptographic Data Lineage

Mutation und sicherheitsrelevante Verwaltungsaktionen erzeugen jetzt einen Append-Only-Provenance-Eintrag. Jeder Eintrag enthält:

- Operation,
- Actor-Signatur,
- Ziel-Signatur,
- Hash des redigierten Payloads,
- vorherigen Event-Hash,
- neuen Event-Hash.

Damit entsteht eine Merkle-artige Kette in:

```text
html/snapshots/provenance.mycelia
```

Neue Engine-Befehle:

```text
provenance_log
provenance_verify
```

Die Ledger-Einträge enthalten keine Passwörter, Auth-Patterns, Content-Blobs oder Direct-Ingest-Sealed-Payloads.

### 4. Localhost Transport Security

Die lokale PHP-zu-Python-Verbindung bleibt Zero-Logic, erhält aber eine zusätzliche Anti-Proxying-Schicht. Die Engine erzeugt beim Start ein lokales Transport-Token:

```text
html/keys/local_transport.token
```

PHP liest dieses Token und sendet es als:

```text
X-Mycelia-Local-Token
```

Optional kann die Engine mit lokalem TLS betrieben werden:

```powershell
$env:MYCELIA_LOCAL_TRANSPORT_TOKEN_REQUIRED="1"
$env:MYCELIA_LOCAL_HTTPS="1"
```

Hilfswerkzeug:

```text
tools/generate_localhost_tls.py
```

Neue Status-API:

```text
local_transport_security_status
```

### 5. Native Library Authenticity

Vor dem Laden nativer DLLs wird ein SHA-256-Authentizitätsmanifest geprüft:

```text
docs/native_library_hashes.json
```

Betroffene Rollen:

```text
core_opencl_driver
native_gpu_envelope
```

Hilfswerkzeug:

```text
tools/generate_native_hash_manifest.py
```

Der Native-Build aktualisiert das Manifest automatisch, wenn Python verfügbar ist. Bei Hash-Mismatch verweigert die Engine im strikten Modus das Laden der betroffenen Library.

Neue Status-API:

```text
native_library_authenticity
```

### 6. Cognitive Denial-of-Service Guard

Das Quantum-Oracle wird durch einen Tension Circuit Breaker geschützt. Die VQE/Quantum-Intuition kann nicht mehr allein durch Spannung beliebig oft ausgelöst werden. Eingeführt wurden:

- Cooldown,
- Token-Bucket,
- Suppression-Zähler,
- maschinenlesbarer Status.

Konfigurierbar über:

```text
MYCELIA_QUANTUM_INTUITION_COOLDOWN_MS
MYCELIA_QUANTUM_INTUITION_BURST
```

Neue Status-API:

```text
quantum_guard_status
```

### Admin-Dashboard

Das Admin-Panel enthält jetzt einen Enterprise-v1.20-Statusbereich. Er prüft in einem Durchlauf:

- SMQL Explain,
- SMQL Query,
- Federation Status,
- Provenance Verify,
- Provenance Log,
- Native Library Authenticity,
- Local Transport Security,
- Quantum Guard.

### Teststand

Die bestehende Testsuite wurde um `tests/test_enterprise_v120_extensions.py` erweitert.

```text
Ran 61 tests

OK (skipped=1)
```

### Sicherheitsbewertung

Version 1.20 erweitert die Strict-VRAM-Residency-Beweiskette um vier produktive Schutzebenen:

1. **Auditierbarkeit:** Provenance Ledger.
2. **Anti-DLL-Hijacking:** Native Hash Manifest.
3. **Anti-Localhost-Proxying:** Local Transport Token / optional TLS.
4. **Anti-GPU-DoS:** Quantum Tension Circuit Breaker.

Das ersetzt keinen externen Memory-Probe. Der Strict-VRAM-Status bleibt weiterhin an den dokumentierten Evidence-Lauf gebunden: Engine im Strict-Modus starten, keine Weboberfläche öffnen, frischen Random-Secret-Probe extern scannen, Report einreichen und `strict_vram_evidence_bundle` prüfen.


---

## v1.20.1 Enterprise Hardening: Perfekter Admin-/Transport-/Native-Sicherheitsmodus

Diese Version schließt die in der Admin-Auswertung sichtbar gewordenen Restpunkte für einen produktionsnahen Enterprise-Betrieb.

### Localhost Transport Security ist standardmäßig aktiv

Die Engine erzwingt jetzt standardmäßig lokales Token-Binding über den Header:

```text
X-Mycelia-Local-Token
```

Der Token liegt in:

```text
html/keys/local_transport.token
```

und wird beim Engine-Start erzeugt. PHP liest denselben Token automatisch und sendet ihn bei jeder Anfrage an `mycelia_platform.py`. Damit ist die lokale HTTP-Schnittstelle nicht mehr nur durch `127.0.0.1`, sondern zusätzlich durch ein pro Installation erzeugtes Shared Secret gebunden.

Der Status muss melden:

```json
{
  "token_binding_enabled": true
}
```

### Native Library Authenticity ist als Fail-Closed-Policy sichtbar

Die Native-Library-Prüfung unterscheidet jetzt sauber zwischen Policy und Trigger:

```json
{
  "fail_closed": true,
  "fail_closed_triggered": false
}
```

`fail_closed=true` bedeutet: Im Strict-/Enterprise-Modus würde eine Hash-Abweichung der DLL den Start beziehungsweise das Laden der Library blockieren. `fail_closed_triggered=false` bedeutet: Die aktuell geladene Library entspricht dem Manifest.

### Admin-/SMQL-Report-Redaction

Admin-Debug-Reports und SMQL-Ergebnisse werden jetzt redaktionell gehärtet. Folgende Felder werden nicht mehr im Dashboard offengelegt:

- `auth_pattern`
- `password`
- `profile_seed`
- `profile_blob`
- `content_seed`
- `content_blob`
- `request_token`
- vollständige `engine_session`-Objekte
- vollständige Signaturen in Debug-Reports

SMQL läuft standardmäßig im Safe-Modus:

```json
{
  "safe_mode": true,
  "redaction_policy": "enterprise-safe-smql-results"
}
```

Rohdaten sind nur noch über expliziten Debug-Modus vorgesehen und sollten in Produktivumgebungen nicht verwendet werden.

### Externe Tools unterstützen Token-Binding

Die folgenden Tools lesen automatisch `html/keys/local_transport.token` oder `MYCELIA_API_TOKEN_FILE` und senden den Token an die Engine:

```text
tools/mycelia_heartbeat_audit.py
tools/mycelia_strict_vram_certify.py
tools/mycelia_federation_sync.py
```

Damit funktionieren Scheduled Heartbeat Audit, Strict-Zertifizierung und Föderationssync auch bei aktiviertem Localhost-Token-Binding.

### Bewertung

Mit v1.20.1 sind die drei Restpunkte aus der Admin-Auswertung korrigiert:

| Punkt | Vorher | v1.20.1 |
|---|---|---|
| Localhost Transport Security | `token_binding_enabled=false` | `token_binding_enabled=true` |
| Native Authenticity | Hash OK, aber `fail_closed=false` | Hash OK und `fail_closed=true` |
| Admin-/SMQL-Debugdaten | auth_pattern/blob/session sichtbar | redigiert |

Die Strict-VRAM-Evidence-Gate-Bewertung bleibt methodisch gleich: Sie gilt pro geprüfter Runtime-Sitzung, wenn Strict-VRAM, negativer externer Random-Secret-Probe, keine Python-Restore-Materialisierung und signierter Heartbeat erfüllt sind.


---

## Projektstand v1.21.21: Media-Attractor-System für Forum, Blogposts und Blog-Erstellung

Projektstand v1.21.21 aktualisiert die Web-Content-Schicht nach den Media-Hotfixes für Forum und Blog. Die ältere Dokumentation v1.20.1 beschrieb bereits Forum, Blog, Direct GPU Ingest, Zero-Logic-Gateway, Strict-VRAM-Evidence und Enterprise-Hardening, enthielt aber noch nicht den vollständigen Media-Pfad für Bilder, Videos und sichere Medienlinks.

### Ziel

Bilder und Videos werden nicht als klassische Webserver-Dateien oder SQL-BLOBs behandelt, sondern als eigene Mycelia-Attraktoren in der Tabelle:

```text
mycelia_media_nodes
```

Ein Medium hängt über `target_signature` an genau einem Zielobjekt:

- Forum-Thread
- Kommentar
- Blog
- Blogpost

Die Anzeige erfolgt über renderbare Media-DTOs mit sicheren `data_uri`-Werten für hochgeladene Bilder beziehungsweise kontrollierten Embed-Informationen für zulässige Medienlinks.

### Implementierter Funktionsumfang

| Bereich | Stand v1.21.21 |
|---|---|
| Forum-Thread erstellen/bearbeiten | Bild oder sicherer Medienlink kann angehängt werden |
| Forum-Thread Detailseite | Media-Galerie wird gerendert |
| Forum-Übersicht | `media_preview` und `media_count` werden ausgeliefert |
| Blog erstellen | Bild oder sicherer Medienlink kann direkt an den Blog gehängt werden |
| Blog bearbeiten | weiteres Medium kann ergänzt werden |
| Blog-Übersichten | Blog-Medien werden als Vorschau gerendert |
| Blogpost erstellen | Bild oder sicherer Medienlink kann angehängt werden |
| Blogpost bearbeiten | weiteres Medium kann ergänzt werden |
| Blogpost Detailseite | Media-Galerie wird gerendert |
| `my_blog.php` | Blog- und Blogpost-Medien werden sichtbar |
| Direct GPU Ingest | Media-Felder bleiben nach Normalisierung erhalten |

### Technischer Kern

Der wichtigste Architekturpunkt liegt in der Direct-Ingest-Normalisierung. Das Browser-Skript `www/assets/direct-ingest.js` liest Uploads als Base64 und versiegelt sie gemeinsam mit den übrigen Formularfeldern im WebCrypto-Envelope. Die Engine öffnet das Paket und normalisiert HTML-Formularnamen in kanonische Engine-Payloads.

Vor dem Fix wurden Media-Felder bei mehreren Operationen verworfen. Dadurch meldete die Engine bei der Anzeige:

```text
query_sql_like: Tabelle=mycelia_media_nodes ... Treffer=0
```

Das war kein reines Renderproblem. Es bedeutete, dass gar kein Media-Node gespeichert wurde.

v1.21.21 führt deshalb eine explizite Media-Feld-Konservierung ein. Relevante Felder sind unter anderem:

```text
media_file_b64
media_file_name
media_mime
media_size_bytes
embed_url
media_embed_url
media_title
```

Diese Felder werden für folgende Direct-Ingest-Operationen weitergereicht:

```text
create_forum_thread
update_forum_thread
create_blog
update_blog
create_blog_post
update_blog_post
```

### Neue beziehungsweise korrigierte Engine-Flüsse

#### Forum-Thread

1. Browser liest Datei oder Medienlink.
2. `direct-ingest.js` versiegelt Formularinhalt.
3. `_normalize_direct_payload()` erhält Media-Felder.
4. `create_forum_thread()` oder `update_forum_thread()` speichert den Thread.
5. `_store_media_from_payload()` erzeugt einen `mycelia_media_nodes`-Attraktor.
6. `get_forum_thread()` und `list_forum_threads()` liefern `media`, `media_preview` und `media_count`.

#### Blog

1. `create_blog` und `update_blog` akzeptieren jetzt Media-Felder.
2. Nach dem Speichern des Blog-Attraktors wird `_store_media_from_payload()` mit `target_type="blog"` ausgeführt.
3. `list_blogs()` und `get_blog()` liefern Media-Daten.
4. `blogs.php`, `blog.php` und `my_blog.php` rendern die Medien.

#### Blogpost

1. `create_blog_post` und `update_blog_post` akzeptieren Media-Felder.
2. `update_blog_post()` akzeptiert sowohl `signature` als auch `post_signature`.
3. Medien werden an die Blogpost-Signatur gebunden.
4. Listen- und Detailseiten erhalten renderbare Media-Vorschauen.

### Sicherheitsgrenzen

Die Media-Erweiterung ändert nicht die grundsätzliche Strict-VRAM-Bewertung. Für die Webanzeige müssen Bilder, Titel, Data-URIs oder Embed-Metadaten an PHP und den Browser zurückgegeben werden. Diese UI-Rekonstruktion ist Teil des Human-Web-UI-Pfads und darf nicht als Strict-VRAM-Evidence-Lauf interpretiert werden.

Für den Audit-Pfad bleibt weiterhin maßgeblich:

1. Engine frisch im Strict-Modus starten.
2. Weboberfläche nicht öffnen.
3. Random-Secret-Memory-Probe extern ausführen.
4. Report einreichen.
5. `strict_vram_evidence_bundle` prüfen.

### Teststand des Media-Fixstands

Die Media-Regressionssuite prüft insbesondere:

- Media-Vorschau in Forum-Listen.
- Media-Vorschau in Blogpost-Listen.
- Direct-Ingest-Update eines Forum-Threads mit Bild.
- Direct-Ingest-Blogpost-Erstellung mit Bild.
- Direct-Ingest-Blogpost-Update mit Embed-Link.
- Blog-Erstellung mit Bild.
- Blog-Bearbeitung mit zusätzlichem Medium.
- Renderbare Blog-Medien in `blogs.php`, `blog.php` und `my_blog.php`.

Aktueller dokumentierter Testlauf:

```text
Ran 8 tests in 2.146s
OK
```

### Bewertung

v1.21.21 verschiebt Medien aus der klassischen Dateianhangslogik in das Mycelia-Attraktormodell. Der Vorteil ist ein einheitliches Content-Modell: Text, Blog, Forum, Reaktionen, Kommentare und Medien laufen über dieselbe Engine-Autorität, denselben Autosnapshot-Pfad und dieselbe Moderationslogik.

Der wichtigste verbleibende Punkt ist Skalierung: Base64-Uploads sind für kleine Bilder praktikabel, erzeugen aber Overhead. Für größere Medien sollte ein späterer Projektstand einen chunked Native-Ingest-Pfad oder einen objektartigen Media-Snapshot-Speicher ergänzen.


---

## 15. Aktualisierung v1.21.21: Enterprise-Evolution, E2EE-Mailbox und Profil-Nachrichten

Der Stand v1.21.21 erweitert die bisherige Plattform über das Media-Attractor-System hinaus um ein vollständigeres Kommunikations- und Sicherheitsmodell. Die Weiterentwicklung betrifft nicht nur eine einzelne Seite, sondern den gesamten Pfad von Browser-Kryptografie, Gateway-Verhalten, Engine-Speicherung, Profil-UX und Snapshot-Verhalten.

### 15.1 Enterprise-Evolution seit v1.21.6

Zwischen v1.21.7 und v1.21.21 wurden acht größere Weiterentwicklungen in das Projekt aufgenommen:

| Bereich | Umsetzung |
|---|---|
| E2EE-Direktnachrichten | Browserseitige Verschlüsselung, Engine speichert blinde Ciphertext-Attraktoren. |
| Forward-Secrecy-Direct-Ingest | Direct-Ingest Phase 2 mit ephemerem Schlüsselaustausch und nativer Envelope-Integration, sofern verfügbar. |
| Kognitives Live-Dashboard | Nutzdatenfreie Telemetrie für Harmony, Tension, Qualia und Systemzustände. |
| Ephemere Daten | TTL-/Decay-Modell für bewusst vergängliche Attraktoren. |
| Multimodale SMQL-Cues | Vektor-Cues für semantische Suche, insbesondere Media-/Signatur-Ähnlichkeit. |
| WebAuthn/FIDO2-Bridge | Vorbereitete Challenge-/Assertion-Integration für passwortärmere Authentifizierungspfade. |
| Memory-Probe-Härtung | Positive Canaries und klassifizierte Probe-Logik gegen blinde oder unvollständige RAM-Snapshots. |
| VRAM-Zeroing-/Constant-Time-Contract | Auditierbarer Vertrag für Buffer-Zeroing und datenunabhängige Native-Pfade. |

Diese Funktionen sind so dokumentiert, dass ihre Sicherheitswirkung nicht als absolute Behauptung formuliert wird. Relevanter ist, welche Daten wo sichtbar werden: PHP erhält bei produktiven Mutationen weiterhin keine Formular- oder Nachrichtenklartexte; die Engine speichert E2EE-Nachrichten als Ciphertext; die Lesbarkeit entsteht erst im Browser des berechtigten Nutzers.

### 15.2 E2EE-Nachrichtenmodell

v1.21.21 führt ein für Anwender nutzbares Nachrichtenmodell ein:

1. Ein Nutzer erzeugt im Browser einen E2EE-Schlüssel.
2. Der öffentliche Schlüssel wird als Public-Key-Attraktor registriert.
3. Andere Nutzer können diesen Schlüssel über das Empfänger-Verzeichnis auswählen.
4. Die Nachricht wird im Browser verschlüsselt.
5. Die Engine speichert eine Inbox-Kopie für den Empfänger und eine Outbox-Kopie für den Sender.
6. Lesen, Antworten und Löschen erfolgen über das Profil-Nachrichtenmenü.

Die Engine muss für den Inhalt einer Nachricht keinen Klartext sehen. Die Nachricht ist für das System ein strukturierter Ciphertext-Attraktor mit Metadaten wie Sender, Empfänger, Nonce, Ciphertext, Key-Referenz und Löschstatus. Damit verschiebt sich das Vertrauensmodell: Die Plattform stellt Zustellung, Rechteprüfung und Persistenz bereit, während die Inhaltsrekonstruktion im Browser erfolgt.

### 15.3 Profil-Nachrichtenmenü

Das Profil enthält ab v1.21.21 ein sichtbares Nachrichtenmenü:

- Nachricht schreiben,
- Inbox,
- Outbox,
- Lesen,
- Antworten,
- Löschen.

Der bisher unpraktische Zustand, bei dem Nutzer Empfänger-Signaturen oder Public-Key-JWKs manuell kopieren mussten, wurde durch ein Empfänger-Verzeichnis ersetzt. Das Profil kann E2EE-fähige Nutzer anzeigen und die Schreibmaske automatisch befüllen. Antworten aus der Inbox übernehmen den Absender als Empfänger.

### 15.4 Zustellmodell

Die Zustellung erfolgt nicht mehr an eine technische Key-Signatur allein, sondern an die Nutzeridentität mit zugeordnetem aktuellem E2EE-Public-Key. Falls alte Formulare noch eine Key-Signatur senden, kann die Engine diese auf den Besitzer auflösen. Dadurch bleibt Rückwärtskompatibilität erhalten, ohne dass die neue UX Signaturen sichtbar machen muss.

### 15.5 Löschmodell

Löschen ist mailbox-seitig modelliert. Das bedeutet: Eine Nachricht kann aus der Inbox oder Outbox eines Nutzers entfernt werden, ohne dass der jeweils andere Mailbox-Zweig automatisch seine Kopie verliert. Dieses Modell entspricht eher modernen Mailbox-Systemen und verhindert, dass ein Sender nachträglich die lokale Inbox-Ansicht eines Empfängers unkontrolliert manipuliert.

### 15.6 Snapshot-Restore-Hotfix

v1.21.12 korrigiert das Snapshot-Restore-Verhalten. Ein leerer Restore-Aufruf darf nicht stillschweigend auf einen zufällig vorhandenen Autosave-Fallback ausweichen. Der leere Restore nutzt jetzt den konfigurierten Snapshot-Pfad und gibt bei fehlender Datei einen sauberen Fehler zurück. Legacy-Pfade behalten ihren gezielten Autosave-Fallback.

### 15.7 Aktueller Reifegrad

Mit v1.21.21 ist MyceliaDB nicht nur eine Forum-/Blog-Plattform mit Media-Attractors, sondern eine SQL-freie Webplattform mit:

- PHP-blindem Gateway,
- verschlüsselter Snapshot-Persistenz,
- Direct-Ingest Phase 1/2,
- Native-VRAM-Auditpfaden,
- E2EE-Mailbox,
- Profil-integrierter Nachrichten-UX,
- Media-Attractor-System,
- SMQL-Erweiterungen,
- Admin-/Plugin-/Datenschutzfunktionen.

Die Sicherheitsqualität wird weiterhin über implementierte Eigenschaften und Tests beschrieben, nicht über absolute oder prozentuale Versprechen.


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
