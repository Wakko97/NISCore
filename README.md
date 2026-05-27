# NISCore – Umsetzung nach OPSCORE_PROJEKTPLAN

Dieses Repository enthält eine **MVP+ Referenzimplementierung** der in `OPSCORE_PROJEKTPLAN.md` beschriebenen Bereiche.

## Umgesetzte Module

- **LF40 Schnittstellen (REST):** Register, Diagnostics, Wipe, Certificate, Webhook
- **LF15 SSL/TLS Monitoring:** Endpoint mit Ablaufbewertung
- **LF65 Handlungsempfehlungen:** Regelbasierte Next-Best-Action-Engine
- **NF10 Revisionssicherheit:** Audit-Events mit Hash-Kette
- **LF50/LF51 Endpoint Security & Incident:** Endpoint-Check inkl. Empfehlungen
- **LF52 Backup/Recovery Vorbereitung:** Empfehlungstypen für Backup-Fehlerfälle
- **LF60 Server Operations:** Server-Health-Check Endpoint
- **LF70 KI-Assistenz:** lokaler Assistenz-Endpoint (Ollama-konformer Betriebsmodus, Human-in-the-loop)
- **LF80 Migration Suite:** Migrationsjobs + SFTP-Endpoint-Verwaltung
- **LF90 Mobile Diagnostics:** Mobile Device Inventur, Assessment und signierter Report-Metadatenfluss
- **Werkstatt ISO-Baustein:** ISO-Build-Endpoint mit Artefakt/Manifest + USB-Toolkit (connect Script) als Pipeline-Grundgerüst
- **GitHub Private Repo Integration:** SSH-Key-Hinterlegung für `git@github.com` Workflows

## Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Kernendpunkte

- `GET /health`
- `POST /api/v1/clients/register`
- `GET /api/v1/clients`
- `GET /api/v1/recommendations`
- `GET /api/v1/migrations/jobs`
- `GET /api/v1/audit/events?limit=100`
- `PATCH /api/v1/clients/{asset_id}`
- `POST /api/v1/diagnostics/results`
- `POST /api/v1/storage/detect`
- `GET /api/v1/storage/devices/{asset_id}`
- `POST /api/v1/storage/wipe`
- `POST /api/v1/wipe/jobs`
- `POST /api/v1/wipe/execution-jobs`
- `POST /api/v1/wipe/execution-jobs/{job_id}/approve`
- `POST /api/v1/wipe/execution-jobs/{job_id}/reject`
- `POST /api/v1/wipe/execution-jobs/{job_id}/cancel`
- `POST /api/v1/wipe/execution-jobs/{job_id}/dispatch`
- `GET /api/v1/wipe/execution-jobs`
- `POST /api/v1/wipe/execution-jobs/{job_id}/agent/build`
  - unterstützt `output_format`: `dir`, `tar.gz`, `zip`
- `GET /api/v1/wipe/certificates/{certificate_id}`
- `POST /api/v1/webhooks/test`
- `POST /api/v1/web/scans/ssl-check`
- `POST /api/v1/security/endpoint-check`
- `POST /api/v1/servers/health-check`
- `POST /api/v1/ai/assist`
- `POST /api/v1/migrations/jobs`
- `PATCH /api/v1/migrations/jobs/{job_id}`
- `POST /api/v1/migrations/jobs/{job_id}/complete`
- `POST /api/v1/sftp/endpoints`
- `POST /api/v1/mobile/devices`
- `POST /api/v1/mobile/assessments`
- `POST /api/v1/workshop/iso/build`
- `POST /api/v1/integrations/github/ssh-key`
- `POST /api/v1/agents/enroll` (Agent/Bootstick Token-Enrollment)
- `POST /api/v1/modules/run` (Modul-Run starten: migration, wipe, hardware, seo, pentest, backup, mobile)
- `POST /api/v1/modules/{run_id}/control` (Pause/Resume/Cancel/Approve/Reject)
- `POST /api/v1/modules/{run_id}/progress` (Fortschritt/Event durch Agent/Operator melden)
- `GET /api/v1/modules/runs` (Filter: `module`, `status`, Pagination)
- `POST /api/v1/modules/{run_id}/tickets/link` (NDesk Ticket einem Vorgang zuordnen)
- `GET /api/v1/modules/{run_id}/tickets` (Ticket-Zuordnungen pro Vorgang)
- `POST /api/v1/modules/offline/bundle` (Offline-Bootstick Bundle für Vorgang erzeugen)
- `POST /api/v1/live/status` (gesichert via `X-Live-Token`)
- `GET /api/v1/live/status` (gesichert via `X-Live-Token`)
- `WS /ws/live/status?token=...` (Live Push für Browser/App)

## Hinweis

Die Umsetzung ist absichtlich modular gehalten, damit Worker/Scanner/Signaturdienst/Queue/PKI schrittweise produktionsreif ergänzt werden können.


## Produktion

- Konfiguration erfolgt über `.env` (siehe `.env.example`).
- App nutzt Request-Logging mit `X-Request-ID` Header und globale Fehlerantworten.
- Health-Endpoint liefert Status, Umgebung und Version.
- Start für Netzwerkbetrieb:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- Schreibende Endpunkte können mit `NISCORE_API_TOKEN` abgesichert werden (Header `X-API-Token`).
- Listen-Endpunkte unterstützen `limit` und `offset` für Pagination.

- CORS ist über `NISCORE_CORS_ORIGINS` steuerbar (CSV, z. B. `https://ops.example.com,https://admin.example.com`).
- `GET /ready` ergänzt Readiness-Prüfung inkl. DB-Check.


## UI/UX

- `GET /admin` liefert ein strukturiertes Ops-Dashboard mit Bereichen für Operations, Migration und Monitoring.
- Token-Eingabe (`X-API-Token`) direkt in der UI für geschützte Write-Requests.
- Integrierte Live-Ausgabe von HTTP-Status + Response Body für schnellere Fehlersuche.


## Production Roadmap umgesetzt (Basis)

- **Auth/RBAC:** Bearer-Token Login (`/api/v1/auth/login`) + Rollen (`admin`, `operator`, `viewer`) für geschützte Endpunkte.
- **Postgres + Alembic:** `NISCORE_DATABASE_URL` auf Postgres-Beispiel und Alembic-Basisstruktur (`alembic/`, `alembic.ini`).
- **Postgres + Alembic:** `NISCORE_DATABASE_URL` auf Postgres-Beispiel und Alembic-Basisstruktur (`alembic/`, `alembic.ini`) inkl. Modul-Orchestrierungstabellen (`0003`).
- **CI:** GitHub Actions Workflow mit `ruff`, `bandit`, `pytest`, `compileall`.
- **Job Queue:** In-Process Queue (`app/jobs.py`) + Job-Status-Endpoint (`/api/v1/jobs/{job_id}`) für lange Tasks.
- **Monitoring:** `/metrics` Endpoint plus Request-Logs.
- **E2E:** Top-5 Business-Flow Tests unter `tests/e2e/test_business_flows.py`.

- **Auth-Hardening:** RBAC-Tests für 401/403 ergänzt und Legacy `X-API-Token` Guard entfernt.
- **Monitoring erweitert:** `/metrics` liefert nun Request-/Queue-Zähler, `/ready` enthält Queue-Tiefe.
- **CI erweitert:** Migration-Check via `alembic upgrade head`.
### NDesk Integration konfigurieren

Für die Anbindung an **NDesk (neuland-service-desk)** müssen folgende Umgebungsvariablen gesetzt sein:

```bash
export NDESK_BASE_URL="https://<ndesk-host>"
export NDESK_API_TOKEN="<token>"
```

Neue Endpunkte:
- `GET /api/v1/integrations/ndesk/assets`
- `POST /api/v1/integrations/ndesk/tickets`
- `GET /api/v1/integrations/ndesk/users`
- `POST /api/v1/integrations/ndesk/users`
- `PATCH /api/v1/integrations/ndesk/users/{user_id}`
- `POST /api/v1/integrations/ndesk/staff-sync`
- `GET /api/v1/integrations/ndesk/tickets` (Ticket-Pull/Abgleich)


## Live-Status Absicherung

Für Live-Status Push/Stream muss ein gemeinsames Secret gesetzt sein:

```bash
export NISCORE_LIVE_TOKEN="<starkes-zufallssecret>"
```

Nur Requests mit korrektem `X-Live-Token` (REST) bzw. `token` Query-Parameter (WebSocket) werden akzeptiert.
