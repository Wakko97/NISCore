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
- **Werkstatt ISO-Baustein:** ISO-Build-Endpoint mit Artefakt/Manifest-Erzeugung als Pipeline-Grundgerüst
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
- `POST /api/v1/wipe/jobs`
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

## Hinweis

Die Umsetzung ist absichtlich modular gehalten, damit Worker/Scanner/Signaturdienst/Queue/PKI schrittweise produktionsreif ergänzt werden können.


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
