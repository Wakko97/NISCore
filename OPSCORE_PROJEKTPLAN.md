# Projektplan für „NISCore“ (IT-Allround & Asset Management Suite)

## 1) Zielbild und Projektumfang
NISCore wird als **zweiteiliges System** umgesetzt:

1. **Zentrales Dashboard (On-Premises)**
   - Verwaltung von Scans, Diagnosen, Löschaufträgen, Zertifikaten, Alarmen.
2. **Werkstatt-Modul (Live-System/Agent)**
   - Hardware-Diagnose, sicheres Löschen, lokales Erfassen von Seriennummern, API-Upload.

Die Lösung priorisiert:
- Revisionssicherheit (Audit-Trail, Signatur/Hash, Unveränderbarkeit),
- schnelle Werkstatt-Prozesse („Ein-Klick-Diagnose“),
- modulare Erweiterbarkeit (Plugin-/Job-Modell),
- klare, automatisch generierte **Handlungsempfehlungen** pro Befund (Next Best Action).

---

## 2) Umsetzungsstrategie (phasenbasiert)

## Phase 0 – Discovery & Architektur-Freeze (2 Wochen)
**Ziele:** Scope finalisieren, Risiken minimieren, Security-Baseline festlegen.

**Ergebnisse:**
- Domänenmodell (Assets, Scans, Jobs, Reports, Wipe-Certificates).
- API-Verträge (OpenAPI) zwischen Zentrale und Client.
- Sicherheitskonzept (RBAC, Verschlüsselung, Signierung, Logging, Backup).
- Tool-Entscheidungen für Scanner und Löschpfade.

**Wichtige Entscheidungen:**
- Welche Pentest-Scanner in Version 1 enthalten sind.
- Ob Live-USB und Agent parallel in MVP unterstützt werden oder zunächst nur Live-USB.
- PKI/Signaturmodell (internes CA-Zertifikat oder HSM-gestützte Signatur).

## Phase 1 – MVP Core (8–10 Wochen)
**Ziele:** End-to-End-kritische Abnahmekriterien vollständig liefern.

**Inhalt MVP:**
- LF11 Portprüfung (Standardports, einfacher Job-Runner).
- LF13 Basis-SEO (Meta, Alt, Broken Links, einfache Performance-Metrik).
- LF15 SSL/TLS Ablaufüberwachung + Alerting.
- LF21 Hardware-Inventur (CPU, RAM, Board/BIOS, GPU, Akku).
- LF22 SMART + NVMe-Lebensdauer + Kurzbenchmark.
- LF31 Löschpfad für SSD/NVMe (Secure Erase/Sanitize, mit Fallback-Strategie).
- LF32 PDF-Zertifikat inkl. Pflichtfelder + SHA-256 Hash + Signatur.
- LF41 API-Upload vom Client zur Zentrale.
- LF42 Webhook-Benachrichtigungen (Teams/Slack).
- LF50 Endgeräteschutz: Malware-/Viren-Indikatoren erkennen (Signatur + Verhalten).
- LF51 Ransomware-Response: Erkennung, Isolierung, Forensik-Snapshot, Wiederherstellungs-Runbook.
- LF52 Backup-Orchestrierung: policybasiertes Backup vor kritischen Eingriffen + Restore-Validierung.
- LF60 Server-Fokus: Health-, Security- und Kapazitätschecks für Windows-/Linux-Server.
- LF70 KI-Assistenz: lokale Ollama-Instanz für Explainability, Priorisierung und Next-Step-Empfehlungen.
- LF80 Migrationssuite: IMAP-Mailmigration, OneDrive→Nextcloud und SFTP-Transferdienst.
- LF90 Mobile Device Diagnostics: Auslesen/Analyse von iOS/Android inkl. Protokollerstellung.

## Phase 2 – Härtung & Compliance (4 Wochen)
**Ziele:** Betriebssicherheit, Nachvollziehbarkeit, Last- und Fehlertoleranz.

**Inhalt:**
- Erweiterte Rollen/Rechte und Mandantentrennung (falls nötig).
- Tamper-evident Audit-Log (append-only, Hash-Kette).
- Revisionsablage & Retention-Regeln.
- Security-Tests, Threat Modeling, Backup/Restore-Test.

## Phase 3 – Ausbau (kontinuierlich)
**Ziele:** Modularität und neue Module ohne Core-Refactor.

**Mögliche Erweiterungen:**
- OWASP-Deep-Scans (LF12 ausgebaut),
- WCAG-/Responsive-Designerweiterung (LF14 ausgebaut),
- Asset-Optimierer für Bilder,
- CMDB-Integration/SSO/AD.

---

## 3) Zielarchitektur (konkret)

## 3.1 Zentrales Dashboard
- **Frontend:** Next.js (Admin UI, Kachel-Ansicht, Job-Status, Berichte, Zertifikatsarchiv).
- **Backend:** FastAPI (REST + Worker-Orchestrierung).
- **Datenbank:** PostgreSQL.
- **Asynchrone Jobs:** Queue (z. B. Redis + RQ/Celery oder PostgreSQL-basierter Worker).
- **Dateiablage:** On-Prem Object Storage / Fileshare für PDFs und Artefakte.
- **Signaturdienst:** interner Signaturservice (Schlüssel strikt serverseitig).

## 3.2 Werkstatt-Modul
- **Variante A (MVP):** Bootbares Debian/Ubuntu-Minimal-Live-System.
- **Variante B (später):** Persistenter Agent (Windows/Linux) für In-Band-Diagnosen.
- **Systemtools:** `smartctl`, `nvme-cli`, `dmidecode`, `lshw`, optional `memtester`.
- **Lokale Sicherheit:** Signed Client-Binary, API-Token mit kurzer Lebensdauer, Zeitstempel.

## 3.3 Integrationsprinzip
- Client erzeugt lokal strukturierte JSON-Ergebnisse.
- JSON wird signiert/über TLS übertragen.
- Zentrale validiert, persistiert, erzeugt Report und Audit-Event.

---

## 4) Moduldesign nach Lastenheft

## LF10 Web & Security
- **Portprüfer (LF11):** konfigurierbare Portlisten, Timeouts, Parallelisierung.
- **Security Audit (LF12):** zunächst Baseline-Checks, später tiefer OWASP-Scan.
- **SEO (LF13):** Crawl-Tiefe begrenzen, robots.txt berücksichtigen, 404-Report.
- **Webdesign-Support (LF14):** HTML/CSS-Validation + Kontrastcheck + Responsive Preview.
- **SSL/TLS (LF15):** Zertifikatskette, Ablaufdatum, Schwellwert-Alarme (z. B. 30/14/7 Tage).

## LF20 Hardware-Diagnose
- Standardisierte Sammelpipeline je Gerät:
  1. Identifikation (Board-SN, Asset-ID),
  2. Sensor-/Komponentendaten,
  3. Speichermedien SMART/NVMe,
  4. Kurzbenchmark,
  5. Ergebnisklassifikation (OK/Warn/Kritisch).

## LF30 Sicheres Löschen & Protokoll
- **Wipe Policy Engine:** Auswahl nach Medientyp (HDD vs SSD/NVMe).
- **Nachweisbarkeit:** Command-Log, Rückgabecodes, Device-Fingerprint.
- **PDF-Zertifikat:** Pflichtfelder + Hash + Signatur + unveränderbare Ablage.

## LF40 Schnittstellen
- REST-Endpunkte:
  - `/api/v1/clients/register`
  - `/api/v1/diagnostics/results`
  - `/api/v1/wipe/jobs`
  - `/api/v1/wipe/certificates`
  - `/api/v1/webhooks/test`

---



## LF50 Endpoint Security & Incident Response
- **Viren-/Malware-Erkennung (LF50):**
  - Kombination aus Signaturchecks (AV/EDR-Engine) und Verhaltensindikatoren (massive Dateiänderungen, Shadow-Copy-Manipulation, ungewöhnliche Prozessketten).
  - Ergebnisse je Host als Severity (Info/Warn/Kritisch) inkl. Handlungsempfehlung.
- **Ransomware-Prüfung & Beseitigung (LF51):**
  - Automatische IOC-Prüfung (Dateiendungen, Lösegeldnotizen, bekannte TTP-Muster).
  - Quarantäne/Isolierung des Endgeräts (Netzwerksegmentierung via RMM/EDR-Schnittstelle).
  - Forensik-Basisdaten sichern (Prozessliste, Persistenz-Artefakte, Event-Logs, optional Memory-Dump).
  - Standardisierte Beseitigungs-Playbooks (Containment → Eradication → Recovery → Lessons Learned).

## LF52 Backup & Recovery
- **Backup-Erstellung:**
  - Vor Wipe/Remediation obligatorischer Pre-Check „letztes valides Backup vorhanden?“.
  - Falls nicht vorhanden: ad-hoc Image-/Dateibackup auslösen (policygesteuert).
- **Restore-Validierung:**
  - Regelmäßige Test-Restores auf Staging-Hosts.
  - Dokumentation von RPO/RTO pro Kunde/Systemklasse im Dashboard.

## LF60 Server Operations (starker Server-Bezug)
- **Server-Fleet-Übersicht:** CPU/RAM/Storage/RAID, Zertifikate, Patchlevel, Backup-Status, Security-Events in einer Kachel.
- **Server-spezifische Checks:**
  - Windows Server: Eventlog-Checks, VSS/Backup-Status, AD-Dienste, Defender-Status.
  - Linux Server: systemd-Service-Health, Journal-Fehler, Paketstand, SSH-Härtung, Dateiintegrität.
- **Wartungsmodus/Change-Fenster:** Scans und Remediation-Jobs berücksichtigen Wartungsfenster pro Servergruppe.



## LF65 Handlungsempfehlungen & Next-Best-Action
- **Empfehlungs-Engine:** Jeder Befund erzeugt automatisch konkrete Maßnahmen mit Priorität, Aufwand und Risiko.
- **Ausgabeformat je Finding:**
  - *Was ist passiert?* (Kurzdiagnose),
  - *Was jetzt?* (1–3 Sofortmaßnahmen),
  - *Was als Nächstes?* (nachgelagerte Schritte),
  - *Automatisierbar?* (ja/nein + Runbook/Script-Link).
- **Beispiele:**
  - SMART kritisch → „Backup sofort starten“, „Datenträger tauschen“, „Ticket P1 eröffnen“.
  - Ransomware-Indikator → „Host isolieren“, „IOC-Sweep starten“, „Restore-Fähigkeit prüfen“.
  - SSL läuft <7 Tage ab → „Zertifikat erneuern“, „Deployment prüfen“, „Ablaufmonitor scharf schalten“.
- **Serverfokus:** Empfehlungen berücksichtigen Rolle des Systems (DC, Hypervisor, DB-Server, Fileserver) und Wartungsfenster.

## LF70 KI-Assistenz (lokale Ollama-Anbindung)
- **Ziel:** KI-Unterstützung ohne Cloud-Zwang, vollständig On-Premises.
- **Anbindung:** Lokale Ollama-API (z. B. `http://ollama.local:11434`) als optionaler Provider in NISCore.
- **Einsatzfälle:**
  - Befunde zusammenfassen (technisch + Management-tauglich),
  - Handlungsempfehlungen priorisieren,
  - Runbook-Schritte in Klartext erklären,
  - Ticketbeschreibung automatisch vorschlagen.
- **Sicherheitsleitplanken:**
  - Keine Rohdaten-Exfiltration nach extern,
  - Prompt-Filter für sensible Daten (PII/Secrets),
  - versionierte Prompt-Templates und Audit-Logging der KI-Ausgaben,
  - Fallback-Betrieb ohne KI muss jederzeit möglich sein.
- **Betriebsmodus:** „Human-in-the-loop“: KI empfiehlt, Techniker gibt final frei.



## LF80 Migrationssuite (Mail & Files)
- **IMAP-Migrator (LF81):**
  - Migration von Postfächern zwischen Quell-/Ziel-IMAP (z. B. Hosted Exchange IMAP, Dovecot, Cyrus, etc.).
  - Unterstützt Delta-Läufe (nur neue/geänderte Mails), Mapping von Ordnerstrukturen und Dry-Run vor Produktivlauf.
  - Validierung über Nachrichtenzahl, Stichproben-Hashing, Fehlerreport pro Postfach.
- **OneDrive → Nextcloud Migration (LF82):**
  - Übernahme von Dateien/Ordnern inkl. Zeitstempel und Berechtigungs-Mapping (soweit technisch möglich).
  - Batch-/Tenant-fähige Läufe mit Wiederaufnahme (Resume) bei Abbruch.
  - Abschlussbericht mit Migrationsquote, Konflikten und manuellen Nacharbeiten.
- **SFTP-Serverdienst (LF83):**
  - Bereitstellung eines verwalteten SFTP-Endpunkts für Migrationspakete, Exporte und Audit-Artefakte.
  - Mandantenfähige Verzeichnisse, Schlüssel-basierte Authentifizierung, IP-Allowlisting, Ablaufregeln für Uploads.
  - Optionales „Drop-Zone“-Konzept für externe Partner/Kunden.

## LF84 Migrations-Orchestrierung & Handlungsempfehlungen
- Vor jedem Lauf automatische Pre-Checks:
  - Konnektivität, Credentials, Quota, API-Limits, Namenskonflikte, Zielspeicherplatz.
- Während des Laufs:
  - Fortschritt, Fehlerrate, Retries, ETA im Dashboard.
- Nach dem Lauf:
  - Konkrete Next Steps je Fehlerklasse (z. B. „Berechtigungsfehler erneut mit Admin-Consent“, „Dateiname normalisieren“, „Mailbox erneut delta-syncen“).



## LF90 Mobile Device Diagnostics & Protokollierung
- **Mobile Inventur (LF91):**
  - Erfassung von iOS-/Android-Geräten (Hersteller, Modell, OS-Version, Speicher, Akkuzustand soweit verfügbar, Gerätestatus).
  - Verwaltung pro Mandant/Kunde inkl. Gerätezuordnung zu Benutzer/Asset.
- **Mobile Sicherheitsanalyse (LF92):**
  - Compliance-Checks: Verschlüsselung aktiv, PIN/Biometrie, Root/Jailbreak-Indikatoren, Patchstand.
  - App-Risikoanalyse anhand Richtlinien (unerlaubte Sideloading-Indikatoren, unsichere Profile, veraltete App-Versionen).
- **Mobile Protokolle/Zertifikate (LF93):**
  - Automatische PDF-Protokolle je Auslese-/Analyse-Lauf (Zeit, Techniker, Gerät, Findings, Handlungsempfehlung).
  - Signatur/Hash analog zu Löschzertifikaten für Revisionssicherheit.
- **Technische Anbindung (LF94):**
  - Integration via MDM/UEM-Schnittstellen (z. B. Intune, Workspace ONE, MobileIron) statt unsicherer Direktzugriffe.
  - Optionaler lokaler Agent nur in BYOD-freier Unternehmensumgebung und mit expliziter Freigabe.

## 5) Datenmodell (vereinfachter Entwurf)
- `assets` (Geräte, Seriennummern, Typ, Status)
- `diagnostic_runs` (Zeitpunkt, Techniker, Ergebnis, Rohdaten-JSON)
- `storage_devices` (Modell, Seriennummer, SMART/NVMe-Metriken)
- `wipe_runs` (Methode, Standard, Status, Logs)
- `certificates` (PDF-Pfad, SHA-256, Signatur-Metadaten)
- `web_scans` (Ziel, Ports, SEO, SSL, Findings)
- `alerts` (Typ, Schweregrad, Kanal, Quittierung)
- `audit_events` (append-only, Nutzeraktion, Hash-Vorgänger)
- `recommendations` (finding_id, Priorität, empfohlene Aktion, Status, Freigabe durch Techniker)
- `ai_assists` (Kontext, Modell, Prompt-Version, Antwort, Freigabestatus, Zeitstempel)
- `migration_jobs` (Typ: IMAP/OneDrive-Nextcloud, Quelle, Ziel, Status, Fortschritt, Start/Ende)
- `migration_items` (Objekt-ID, Pfad/Message-ID, Ergebnis, Fehlercode, Retry-Zähler)
- `sftp_endpoints` (Mandant, Host, Key-Fingerprint, Policy, Ablaufdatum)
- `mobile_devices` (OS, Modell, Seriennummer/UDID, Ownership, Compliance-Status)
- `mobile_assessments` (Gerät, Checkprofil, Findings, Risiko, Maßnahmen)
- `mobile_reports` (PDF-Pfad, Hash, Signatur, Lauf-ID, Techniker)

---

## 6) Sicherheits- und Compliance-Konzept (NF10)
- On-Prem-Deployment ohne Cloud-Zwang.
- TLS intern (mTLS bevorzugt für Client↔API).
- Rollenmodell: Admin, Security Analyst, Technician, Auditor (Read-only).
- PDF-Zertifikate mit kryptografischer Integrität (Hash + Signatur).
- Revisionssichere Ablage mit Aufbewahrungsfristen.
- DSGVO: Datenminimierung, Löschkonzept, Protokollierung von Zugriffen.
- **Privacy by Design/Default:** Standardmäßig nur notwendige technische Metadaten erfassen, keine privaten Inhalte (z. B. Mail-Inhalte, Chat, Fotos).
- **Mandantentrennung:** strikte logische Trennung je Kunde inkl. verschlüsselter Datenräume und getrennten API-Scopes.
- **Verschlüsselung:** At-Rest (DB, Objektablage, Backups) + In-Transit (TLS/mTLS), Schlüsselrotation und HSM/KMS-Option.
- **Aufbewahrung & Löschung:** konfigurierbare Retention je Artefaktklasse (Scans, Protokolle, Forensik, Migration) inkl. rechtssicherem Löschlauf.
- **Rechte & Nachvollziehbarkeit:** Vier-Augen-Freigabe für kritische Aktionen (Wipe, Isolation, Massenmigration), unveränderbares Audit-Logging.

---

## 7) Umsetzungsablauf „von Orchestrierung zu produktiven Fachmodulen“ (aktueller Delivery-Plan)

> Ausgangslage: API-Orchestrierung ist vorhanden (`/api/v1/modules/run`, Progress/Control/Listing), die Fach-Engines werden nun in einem priorisierten Ablauf ergänzt.

### Phase A – Fundament stabilisieren (Sprint 1–2)

1. **Modul-Contract pro Domäne finalisieren**
   - Einheitliches `RunInput`/`RunOutput`-Schema je Modul (migration, wipe, hardware, seo, pentest, backup).
   - Definition standardisierter Statusübergänge (`queued → running → paused → completed|failed|canceled`).
   - Pro Modul ein verbindliches Evidenz-Format (Nachweise, Artefakte, Prüfsummen, Quellen).
2. **Persistenz entkoppeln**
   - Ablösung des `result_json`-Monoliths durch modul-spezifische Ergebnistabellen.
   - Einführung von Retry-, Dead-letter- und Sync-Metadaten als eigene Entitäten.
3. **Audit-Härtung**
   - Erweiterung der Hash-Chain um fachliche Evidenz-Referenzen pro Einzelschritt.
   - Signatur-/Vertrauensmodell für Offline-Importe festlegen (Trust Store + Signaturprüfung).

### Phase B – NDesk- und Agent-Lifecycle schließen (Sprint 2–3)

1. **NDesk bidirektional pro Vorgang**
   - Inkrementeller Delta-Sync mit Cursor-Handling und Konfliktstrategie (Last-Writer/Policy-basiert).
   - Inbound-Webhook-Receiver für Ticket-Events und Mapping auf bestehende Runs/Cases.
   - Zustandskopplung Ticketstatus ↔ Runstatus inkl. Fehlerpfad, Retry-Regeln und Idempotenz.
2. **Agent-Lifecycle komplettieren**
   - Heartbeat/Lease-Protokoll mit Timeout, Grace-Period und Session-Recovery.
   - Token-Rotation und Revocation-Liste für kompromittierte/abgelaufene Agenten.
   - Command-Pull/Ack-Modell (at-least-once + deduplizierende Command-IDs).
   - Versioniertes Rollout der Agent-Binaries (MSI/EXE) mit Ring-Deployment (canary → broad).
3. **Offline-Sync-Basis**
   - Store-and-Forward-Mechanik mit Konfliktauflösung (Server-Revision vs. Client-Revision).
   - Reconnect-Sync in zentrale Audit-Chain mit deterministischer Reihenfolge.

### Phase C – Offline-Bootstick produktionsfähig machen (Sprint 3–4)

1. **Signierte Jobpakete**
   - Bundle-Erzeugung als signiertes Offline-Manifest (Tamper-Schutz + Ablaufzeit).
2. **Lokales Journal**
   - Event-Journal auf Bootmedium (append-only, hashverkettet, exportierbar).
3. **Modulspezifische Offline-Ausführung**
   - Ausführungspipelines je Modul statt reiner Bundle-Datei.
   - Wiederanlauf nach Unterbrechung mit Checkpointing.

### Phase D – Fachliche Umsetzung je Modul (Sprint 4–8)

1. **Migration (M365/OneDrive/GoogleDrive/Nextcloud/Mail)**
   - Echte Connectoren, Mapping-Layer, Delta-Sync, Cutover-Runbooks, Verifikationsberichte.
2. **BSI-Wipe + Zertifikate**
   - BSI-Profilbibliothek, medientypspezifische Verfahren (HDD/SSD/NVMe), Compliance-Matrix.
3. **Hardware-Analyse via Agent/Bootmedium**
   - Tiefere Collector-Pipelines (Windows/Linux/Bootstick), Diagnoseprofile, Vergleichsbasis.
4. **SEO/Webanalyse**
   - Crawl-Engine, technische Metriken, Priorisierung und Scorecards.
5. **Pentesting-Automation**
   - Scope-Guardrails, automatisierte Recon-/Validierungskette, sichere Exploit-Validierung.
6. **Backup/Restore via Agent**
   - Backup-Jobs, Restore-Workflows, Drill-Runs, Verify-Schritte, Retention-Policies.

### Phase E – UI, Betrieb und Qualitätssicherung (Sprint 6–9, überlappend)

1. **Webpanel-Ausbau**
   - Laufende Modulansichten mit Timeline/ETA, Fehlerzuständen und Operator-Aktionen.
   - Offline-Bundle- und Sync-Status inklusive Konfliktindikatoren.
2. **Testtiefe ausbauen**
   - Negative RBAC-Tests, Concurrency-/Race-Condition-Szenarien, Duplicate-Guards.
   - Integrationsfehlerbilder für NDesk (HTTP-Timeout, 4xx/5xx, partielle Responses).
   - Migrationstest `alembic upgrade head` als verbindlicher CI-Gate.
3. **Abnahme-Checklisten je Modul**
   - Funktionalität, Sicherheit, Revisionsnachweis, Wiederanlauf, Support-Runbook.

### Definition of Done (quer über alle Phasen)

- **Technisch:** Modul kann orchestriert, pausiert, fortgesetzt, abgebrochen und nachvollziehbar auditiert werden.
- **Betrieblich:** Monitoring, Alerting, Retry/Dead-letter und On-Call-Runbook vorhanden.
- **Compliance:** Evidenzformat, Signaturkette und Prüfpfad für Auditoren dokumentiert.
- **Integration:** NDesk-Status ist pro Vorgang synchron und konfliktfest.
- **Qualität:** E2E- und Negativtests sind grün, inkl. Migrations- und Offline-Reconnect-Szenarien.

---

## 7) UX-/Bedienkonzept (NF20)
- Dashboard-Startseite als Kachel-Dashboard:
  - „Scans starten“, „Werkstatt-Läufe“, „Zertifikate“, „Warnungen“.
- Werkstatt-Flow als 3 Buttons:
  1. Diagnose,
  2. Wipe,
  3. Upload + Zertifikat.
- Ampelstatus pro Ergebnis (grün/gelb/rot), klare Handlungsempfehlungen.

---

## 8) Test- und Abnahmeplan (aus Kriterien abgeleitet)

## Abnahmetest A – Domain Scan
- Eingabe einer Domain.
- Nachweis: offene Ports + SEO-Fehlerbericht + SSL-Status im Dashboard sichtbar.

## Abnahmetest B – Live-Boot Notebook
- Boot über Live-System auf x86_64 Notebook.
- Vollständige HW-Erkennung inkl. Akku und Datenträgern.
- Erfolgreicher API-Upload in die Zentrale.

## Abnahmetest C – SSD Krypto-Erase + Zertifikat
- Durchführung Secure-Erase/Sanitize.
- Ergebnis erfolgreich inkl. Geräte-Seriennummer im Zertifikat.
- PDF im zentralen Archiv inklusive Hash/Signatur prüfbar.

---

## 9) Risiken und Gegenmaßnahmen
- **NVMe/ATA-Kompatibilität variiert:** Geräte-Matrix + Fallback-Prozeduren.
- **False Positives bei Webscans:** regelbare Sensitivität + manuelle Verifikation.
- **Live-System Treiberprobleme:** Hardware-Kompatibilitätsliste, Kernel-Varianten.
- **Schlüsselmanagement für Signatur:** klare PKI-Prozesse, Rotation, Backup.

---

## 10) Team- und Rollenplanung
- Product Owner (Fachabnahme).
- Tech Lead (Architektur, Security).
- 2x Full-Stack (Next.js/FastAPI).
- 1x Systems Engineer (Live-System, Hardware-Tools).
- 1x QA/Compliance (Abnahme, Audit, Dokumentation).

---

## 11) Roadmap (Beispiel, 16 Wochen)
- **W1–W2:** Discovery, Architektur, API-Verträge.
- **W3–W6:** Dashboard-Grundgerüst, Auth, Job-Engine, erste Scanner.
- **W7–W10:** Werkstatt-Modul Diagnose + Upload + Zertifikatsdienst.
- **W11–W12:** Wipe-Workflows HDD/SSD/NVMe, Fehlerpfade.
- **W13–W14:** Alerts, UX-Polish, Rollenmodell.
- **W15–W16:** Abnahmetests, Härtung, Go-Live-Readiness.

---

## 12) Zusätzliche Integrationen für den Alltag im IT-Systemhaus
Zur Entlastung im Tagesgeschäft sollte NISCore neben dem Lastenheft folgende Integrationen als priorisierte Add-ons erhalten:

### A) Ticketing-Integration (hoher Hebel)
- Anbindung an **Jira Service Management**, **Zammad**, **OTRS** oder **Freshservice**.
- Automatische Ticketerstellung aus Findings (z. B. SMART-kritisch, Zertifikat läuft in <14 Tagen ab).
- Rücksynchronisation des Ticketstatus in NISCore (Offen/In Arbeit/Erledigt).

### B) RMM-/Monitoring-Anbindung
- Webhooks/REST für **Checkmk**, **PRTG**, **Zabbix**, **Icinga** oder **NinjaOne**.
- Übergabe von Diagnosedaten als Host-Events.
- Nutzung bestehender Alarmierungswege statt Parallelstrukturen.

### C) AD/Entra/SSO + Rollenmapping
- SSO per **OIDC/SAML** (z. B. Microsoft Entra ID, Keycloak, AD FS).
- Rollenmapping auf Teams (Technik, Security, Audit).
- Deutlich weniger Pflegeaufwand bei Benutzerverwaltung.

### D) CMDB-/Inventar-Sync
- Synchronisation mit **i-doit**, **GLPI**, **Snipe-IT** oder ServiceNow-CMDB.
- Seriennummern, Gerätezustände, Löschzertifikate automatisch an Assets anhängen.
- Vermeidung doppelter Stammdatenpflege.

### E) Backup- und Restore-Checks
- API-Integration mit **Veeam**, **Acronis** oder Nakivo.
- Sichtbarkeit, ob für betroffene Systeme aktuelle Backups vorhanden sind.
- Freigaberegel: kritische Wipe-Jobs nur mit bestätigtem Backup-Status.

### F) Patch- & Vulnerability-Management
- Koppelung mit **WSUS/Intune/SCCM** und Schwachstellenquellen (z. B. OpenVAS/Nessus-Export).
- Priorisierung nach Business-Risiko (CVSS + Asset-Kritikalität).
- Automatische Wartungsaufgaben für veraltete Komponenten.

### G) Remote-Support-/Skripting-Bridge
- Trigger für Standardmaßnahmen (Treibercheck, Cleanup, Health-Check) über PowerShell/Bash.
- Integration in bestehende Fernwartung (z. B. AnyDesk/TeamViewer Connector-Ebene).
- Schnellere Erstbearbeitung im 1st/2nd Level.

### H) Reporting für Kunde & Audit
- Mandantenfähige Reportvorlagen (Management, Technik, Audit).
- Monatliche Auto-Reports per E-Mail/PDF inkl. KPI-Entwicklung.
- Exportformate: PDF, CSV, JSON.

### I) Lokale KI-Integration (Ollama)
- Optionale Anbindung einer lokalen Ollama-Instanz zur Generierung von Handlungsempfehlungen.
- Nutzung für Ticket-Entwürfe, Befund-Zusammenfassungen und priorisierte Next Steps.
- KI-Ausgaben mit Freigabe-Workflow (Techniker/Lead) vor operativer Ausführung.

### J) IMAP-Migrationsanbindung
- Connectoren für Quell-/Ziel-IMAP inklusive Secure-Credential-Handling.
- Batch-Migration pro Kunde/Mandant mit Delta-Synchronisierung.
- Postfach-Validierung und Ausnahmeberichte für Service-Desk-Nacharbeit.

### K) OneDrive → Nextcloud Connector
- OAuth-basierte OneDrive-Anbindung + Nextcloud WebDAV/OCS API als Ziel.
- Mapping-Regeln für Pfade, Dateikonflikte und Nutzerzuordnung.
- Wiederanlaufbare Migrationsjobs mit Fortschrittsanzeige.

### L) Managed SFTP-Service
- SFTP-Endpunkt für Import/Export, inkl. SSH-Key-Management.
- Mandantenisolierung und IP-Restriktionen.
- Automatische Bereinigung per Retention-Policy.

## 13) Priorisierung der Integrationen (empfohlene Reihenfolge)
1. Ticketing + SSO/Role Mapping
2. CMDB-/Inventar-Sync
3. RMM-/Monitoring-Anbindung
4. Patch/Vulnerability
5. Backup-Checks
6. Lokale KI-Assistenz (Ollama)
7. IMAP-Migration
8. OneDrive→Nextcloud-Migration
9. Managed SFTP-Service
10. Reporting-Automation

Damit liefert NISCore früh messbaren Mehrwert im Daily Business (weniger manuelle Übergaben, weniger Medienbrüche, schnellere Entstörung).


## 14) Prüfung: Anbindung an `Wakko97/neuland-service-desk`
Status der Vorprüfung: **technisch einplanen, aber Repository-Zugriff/Verfügbarkeit verifizieren**.

Empfohlener Integrationsansatz (falls API/Webhooks vorhanden):
1. Ereignis in NISCore (z. B. Ransomware-Kritisch, Server-Backup fehlgeschlagen) erzeugt Incident-Payload.
2. Übergabe an Neuland Service Desk via REST/Webhook (Ticket erstellen inkl. Asset-ID, Severity, Runbook-Link).
3. Ticketstatus zurück nach NISCore synchronisieren (Offen/In Bearbeitung/Gelöst).
4. Abschluss mit Audit-Verknüpfung: Incident-ID ↔ Zertifikat/Diagnose-Run.

Pflicht-Checkliste vor Produktivkopplung:
- Auth-Verfahren (API-Key/OAuth2), Rollen- und Mandantenfähigkeit.
- Datenmodell-Mapping (Asset, Kunde, Priorität, SLA).
- Idempotenz (kein Dubletten-Ticketing bei Retries).
- Fehlerpfade/Retry/Dead-Letter-Queue.
- DSGVO & Löschfristen in beiden Systemen konsistent.
