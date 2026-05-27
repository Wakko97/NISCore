from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from sqlmodel import select

from app.config import settings
from app.db import get_session, init_db
from app.models import (
    LiveStatusEvent,
    Alert,
    Asset,
    AuditEvent,
    Certificate,
    DiagnosticRun,
    MigrationJob,
    MobileAssessment,
    MobileDevice,
    MobileReport,
    Recommendation,
    StorageDevice,
    SFTPEndpoint,
    WebScan,
    WipeRun,
)
from app.schemas import (
    AIAssistRequest,
    ClientRegisterRequest,
    ClientUpdateRequest,
    DiagnosticResultRequest,
    EndpointCheckRequest,
    MigrationJobRequest,
    MigrationJobUpdateRequest,
    MobileAssessmentRequest,
    MobileDeviceRequest,
    SFTPEndpointRequest,
    SSLCheckRequest,
    ServerHealthRequest,
    ISOBuildRequest,
    GitHubSSHKeyRequest,
    WebhookTestRequest,
    WipeJobRequest,
    NdeskTicketCreateRequest,
    NdeskUserRequest,
    NdeskUserUpdateRequest,
    LiveStatusEventRequest,
    StorageDetectRequest,
    StorageWipeRequest,
    LoginRequest,
)
from app.services import (
    NdeskClientError,
    hash_chain,
    ndesk_request,
    recommend_for_finding,
    detect_storage_devices,
    build_device_fingerprint,
    secure_equals,
    sign_like,
    ssl_days_until_expiry,
)
from app.frontend import admin_html
from app.jobs import enqueue, get_job, jobs
from app.observability import logger, request_logging_middleware
from app.metrics import render_metrics
from app.security import AuthContext, issue_token, require_role

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.middleware("http")(request_logging_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class LiveStatusHub:
    def __init__(self) -> None:
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        stale: list[WebSocket] = []
        for conn in self.connections:
            try:
                await conn.send_json(message)
            except RuntimeError:
                stale.append(conn)
        for conn in stale:
            self.disconnect(conn)


live_status_hub = LiveStatusHub()


def _require_live_token(x_live_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("NISCORE_LIVE_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="live status token not configured")
    if not x_live_token or not secure_equals(x_live_token, expected):
        raise HTTPException(status_code=401, detail="invalid live status token")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "path": request.url.path})


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_error path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"error": "internal server error", "path": request.url.path})


@app.get("/", response_class=HTMLResponse)
def landing_page() -> str:
    return """
<!doctype html>
<html lang='de'>
<head>
  <meta charset='UTF-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />
  <title>NISCore Control Plane</title>
  <style>
    :root { color-scheme: dark; --bg:#0b1020; --bg2:#121a33; --text:#e8ecff; --muted:#a8b1d8; --accent:#7aa2ff; --ok:#2dd4bf; }
    body { margin:0; font-family: Inter, ui-sans-serif, system-ui; background: radial-gradient(circle at top,#1a2650,var(--bg)); color:var(--text); }
    .wrap { max-width: 980px; margin: 48px auto; padding: 0 20px; }
    .hero { background: linear-gradient(135deg,rgba(122,162,255,.18),rgba(45,212,191,.14)); border:1px solid #2a3768; border-radius:20px; padding:28px; box-shadow:0 10px 30px rgba(0,0,0,.25); }
    h1 { margin:0 0 10px; font-size: clamp(28px,4vw,40px); }
    p { margin:0; color:var(--muted); }
    .grid { margin-top:20px; display:grid; grid-template-columns: repeat(auto-fit,minmax(230px,1fr)); gap:14px; }
    .card { background: var(--bg2); border:1px solid #26325c; border-radius:14px; padding:16px; }
    .card h3 { margin:0 0 8px; font-size:16px; color:var(--accent);} .kpi {color:var(--ok); font-weight:600;}
    a { color:#b8c8ff; }
  </style>
</head>
<body>
  <main class='wrap'>
    <section class='hero'>
      <h1>NISCore – Modernes Operations Dashboard</h1>
      <p>Security, Diagnostics, Wipe-Certificates, Migrationen und Mobile Assessments in einer API-zentrierten Plattform.</p>
      <div class='grid'>
        <article class='card'><h3>API Status</h3><div class='kpi'>/health → ok</div></article>
        <article class='card'><h3>Dokumentation</h3><a href='/docs'>Interaktive Swagger UI</a></article>
        <article class='card'><h3>Version</h3><div class='kpi'>""" + settings.app_version + """</div></article>
      </div>
    </section>
  </main>
</body>
</html>
"""


@app.get("/admin")
def admin_dashboard():
    return admin_html()


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    return PlainTextResponse(render_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get("/ready")
def ready() -> dict:
    with get_session() as session:
        session.exec(select(AuditEvent).limit(1)).all()
    return {"status": "ready", "db": "ok", "version": settings.app_version, "queue_depth": len(jobs)}


@app.get("/health")
def health() -> dict:
    with get_session() as session:
        session.exec(select(Asset).limit(1)).all()
    return {"status": "ok", "env": settings.env, "version": settings.app_version}


@app.post("/api/v1/auth/login")
def login(payload: LoginRequest) -> dict:
    if payload.role not in {"admin", "operator", "viewer"}:
        raise HTTPException(status_code=400, detail="invalid role")
    if not settings.api_token:
        raise HTTPException(status_code=503, detail="auth credentials not configured")
    if not secure_equals(payload.password, settings.api_token):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = issue_token(username=payload.username, role=payload.role, ttl_minutes=120)
    return {"access_token": token, "token_type": "bearer", "role": payload.role}


@app.get("/api/v1/auth/me")
def me(ctx: AuthContext = Depends(require_role("admin", "operator", "viewer"))) -> dict:
    return {"username": ctx.username, "role": ctx.role}


@app.get("/api/v1/clients")
def list_clients(limit: int = 50, offset: int = 0) -> list[dict]:
    limit = 1 if limit < 1 else min(limit, 500)
    offset = 0 if offset < 0 else offset
    with get_session() as session:
        assets = session.exec(select(Asset).order_by(Asset.id.desc()).offset(offset).limit(limit)).all()
    return [a.model_dump() for a in assets]


@app.get("/api/v1/recommendations")
def list_recommendations(limit: int = 50, offset: int = 0) -> list[dict]:
    limit = 1 if limit < 1 else min(limit, 500)
    offset = 0 if offset < 0 else offset
    with get_session() as session:
        recommendations = session.exec(select(Recommendation).order_by(Recommendation.id.desc()).offset(offset).limit(limit)).all()
    return [r.model_dump() for r in recommendations]


@app.get("/api/v1/migrations/jobs")
def list_migration_jobs(limit: int = 50, offset: int = 0) -> list[dict]:
    limit = 1 if limit < 1 else min(limit, 500)
    offset = 0 if offset < 0 else offset
    with get_session() as session:
        jobs = session.exec(select(MigrationJob).order_by(MigrationJob.id.desc()).offset(offset).limit(limit)).all()
    return [j.model_dump() for j in jobs]


@app.get("/api/v1/audit/events")
def list_audit_events(limit: int = 100) -> list[dict]:
    limit = 1 if limit < 1 else min(limit, 500)
    with get_session() as session:
        events = session.exec(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)).all()
    return [e.model_dump() for e in events]


def _create_recommendation(session, finding_type: str, details: str) -> Recommendation:
    finding = recommend_for_finding(finding_type, details)
    rec = Recommendation(finding_type=finding_type, priority=finding["priority"], action=finding["action"], risk=finding["risk"])
    session.add(rec)
    return rec


def _append_audit(session, user: str, action: str, payload: str) -> None:
    last_event = session.exec(select(AuditEvent).order_by(AuditEvent.id.desc())).first()
    prev_hash = last_event.current_hash if last_event else "GENESIS"
    created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    current_hash = hash_chain(prev_hash, f"{action}:{payload}", created_at)
    session.add(AuditEvent(user=user, action=action, payload=payload, prev_hash=prev_hash, current_hash=current_hash, created_at=created_at))


@app.post("/api/v1/clients/register", dependencies=[Depends(require_role("admin", "operator"))])
def register_client(payload: ClientRegisterRequest) -> dict:
    with get_session() as session:
        asset = Asset(**payload.model_dump(), status="registered")
        session.add(asset)
        _append_audit(session, "system", "client_register", payload.model_dump_json())
        session.commit()
        session.refresh(asset)
    return {"id": asset.id, "asset_id": asset.asset_id}


@app.patch("/api/v1/clients/{asset_id}", dependencies=[Depends(require_role("admin", "operator"))])
def update_client(asset_id: str, payload: ClientUpdateRequest) -> dict:
    with get_session() as session:
        asset = session.exec(select(Asset).where(Asset.asset_id == asset_id)).first()
        if not asset:
            raise HTTPException(status_code=404, detail="asset not found")
        updates = payload.model_dump(exclude_none=True)
        for key, value in updates.items():
            setattr(asset, key, value)
        session.add(asset)
        _append_audit(session, "system", "client_update", f"{asset_id}:{updates}")
        session.commit()
        session.refresh(asset)
    return asset.model_dump()


@app.post("/api/v1/diagnostics/results", dependencies=[Depends(require_role("admin", "operator"))])
def upload_diagnostics(payload: DiagnosticResultRequest) -> dict:
    with get_session() as session:
        asset = session.exec(select(Asset).where(Asset.asset_id == payload.asset_id)).first()
        if not asset:
            raise HTTPException(status_code=404, detail="asset not found")
        run = DiagnosticRun(asset_id=asset.id, technician=payload.technician, result=payload.result, raw_json=payload.raw_json)
        session.add(run)
        rec = _create_recommendation(session, payload.result, payload.raw_json)
        _append_audit(session, payload.technician, "diagnostic_upload", payload.model_dump_json())
        session.commit()
        session.refresh(run)
        session.refresh(rec)
    return {"diagnostic_run_id": run.id, "recommendation_id": rec.id}




@app.post("/api/v1/storage/detect", dependencies=[Depends(require_role("admin", "operator"))])
def detect_storage(payload: StorageDetectRequest) -> dict:
    with get_session() as session:
        asset = session.exec(select(Asset).where(Asset.asset_id == payload.asset_id)).first()
        if not asset:
            raise HTTPException(status_code=404, detail="asset not found")

        devices = detect_storage_devices(asset.asset_id, asset.serial_number, asset.device_type)
        stored: list[dict] = []
        for device in devices:
            row = StorageDevice(asset_id=asset.id, **device)
            session.add(row)
            session.flush()
            stored.append({"id": row.id, **device})

        _append_audit(session, "technician", "storage_detect", payload.model_dump_json())
        session.commit()
    return {"asset_id": payload.asset_id, "detected": stored}


@app.get("/api/v1/storage/devices/{asset_id}", dependencies=[Depends(require_role("admin", "operator", "viewer"))])
def list_storage_devices(asset_id: str) -> dict:
    with get_session() as session:
        asset = session.exec(select(Asset).where(Asset.asset_id == asset_id)).first()
        if not asset:
            raise HTTPException(status_code=404, detail="asset not found")
        devices = session.exec(select(StorageDevice).where(StorageDevice.asset_id == asset.id).order_by(StorageDevice.id.desc())).all()
    return {"asset_id": asset_id, "devices": [d.model_dump() for d in devices]}


@app.post("/api/v1/storage/wipe", dependencies=[Depends(require_role("admin", "operator"))])
def wipe_storage_device(payload: StorageWipeRequest) -> dict:
    with get_session() as session:
        asset = session.exec(select(Asset).where(Asset.asset_id == payload.asset_id)).first()
        if not asset:
            raise HTTPException(status_code=404, detail="asset not found")

        disk = session.exec(select(StorageDevice).where(StorageDevice.asset_id == asset.id, StorageDevice.serial_number == payload.serial_number)).first()
        if not disk:
            raise HTTPException(status_code=404, detail="storage device not found")

        command_log = f"wipe --method {payload.method} --standard {payload.standard} --serial {payload.serial_number}"
        run = WipeRun(
            asset_id=asset.id,
            method=payload.method,
            standard=payload.standard,
            status="completed",
            command_log=command_log,
            device_fingerprint=build_device_fingerprint(payload.asset_id, payload.serial_number, payload.method, payload.standard),
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        sha, signature = sign_like(f"{payload.asset_id}:{payload.serial_number}:{run.id}:{command_log}")
        cert = Certificate(wipe_run_id=run.id, sha256=sha, signature=signature, pdf_path=f"/certs/wipe_{run.id}.pdf")
        session.add(cert)
        _append_audit(session, "technician", "storage_wipe", payload.model_dump_json())
        session.commit()
        session.refresh(cert)

    return {"wipe_run_id": run.id, "certificate_id": cert.id, "sha256": cert.sha256}

@app.post("/api/v1/wipe/jobs", dependencies=[Depends(require_role("admin", "operator"))])
def create_wipe_job(payload: WipeJobRequest) -> dict:
    with get_session() as session:
        asset = session.exec(select(Asset).where(Asset.asset_id == payload.asset_id)).first()
        if not asset:
            raise HTTPException(status_code=404, detail="asset not found")
        run = WipeRun(asset_id=asset.id, method=payload.method, standard=payload.standard, status="completed", command_log=f"wipe {payload.method} {payload.standard}", device_fingerprint=f"{asset.asset_id}:{asset.serial_number}")
        session.add(run)
        session.commit()
        session.refresh(run)
        sha, signature = sign_like(f"{asset.asset_id}:{run.id}:{run.command_log}")
        cert = Certificate(wipe_run_id=run.id, sha256=sha, signature=signature, pdf_path=f"/certs/wipe_{run.id}.pdf")
        session.add(cert)
        _append_audit(session, "technician", "wipe_run", payload.model_dump_json())
        session.commit()
        session.refresh(cert)
        run_id = run.id
        cert_id = cert.id
        cert_sha = cert.sha256
    return {"wipe_run_id": run_id, "certificate_id": cert_id, "sha256": cert_sha}
@app.get("/api/v1/wipe/certificates/{certificate_id}")
def get_certificate(certificate_id: int) -> dict:
    with get_session() as session:
        cert = session.get(Certificate, certificate_id)
        if not cert:
            raise HTTPException(status_code=404, detail="certificate not found")
    return cert.model_dump()


@app.post("/api/v1/webhooks/test", dependencies=[Depends(require_role("admin", "operator"))])
def webhook_test(payload: WebhookTestRequest) -> dict:
    with get_session() as session:
        alert = Alert(alert_type="webhook_test", severity="info", channel=payload.channel)
        session.add(alert)
        _append_audit(session, "system", "webhook_test", payload.model_dump_json())
        session.commit()
        session.refresh(alert)
    return {"delivered": True, "alert_id": alert.id}


@app.post("/api/v1/web/scans/ssl-check")
def ssl_check(payload: SSLCheckRequest) -> dict:
    days = ssl_days_until_expiry(payload.host, payload.port)
    severity = "critical" if days < 7 else "warning" if days < 14 else "info"
    rec = recommend_for_finding("ssl_expiry", f"expires in {days} days") if days < 30 else None
    return {"host": payload.host, "days_until_expiry": days, "severity": severity, "recommendation": rec}


@app.post("/api/v1/security/endpoint-check", dependencies=[Depends(require_role("admin", "operator"))])
def endpoint_check(payload: EndpointCheckRequest) -> dict:
    with get_session() as session:
        scan = WebScan(target=payload.asset_id, scan_type=payload.scan_type, findings=payload.details, severity="warning")
        session.add(scan)
        rec = _create_recommendation(session, payload.scan_type, payload.details)
        _append_audit(session, "security", "endpoint_check", payload.model_dump_json())
        session.commit()
        session.refresh(scan)
        session.refresh(rec)
    return {"scan_id": scan.id, "recommendation_id": rec.id}


@app.post("/api/v1/servers/health-check", dependencies=[Depends(require_role("admin", "operator"))])
def server_health(payload: ServerHealthRequest) -> dict:
    with get_session() as session:
        scan = WebScan(target=payload.asset_id, scan_type=f"server_{payload.platform}", findings=payload.metrics_json, severity="info")
        session.add(scan)
        rec = _create_recommendation(session, "server_health_warn", payload.metrics_json)
        _append_audit(session, "ops", "server_health_check", payload.model_dump_json())
        session.commit()
        session.refresh(scan)
        session.refresh(rec)
    return {"health_scan_id": scan.id, "recommendation_id": rec.id}


@app.post("/api/v1/ai/assist")
def ai_assist(payload: AIAssistRequest) -> dict:
    rec = recommend_for_finding(payload.finding_type, payload.details)
    return {"provider": "ollama-local", "human_in_the_loop": True, "summary": f"Kontext: {payload.context}", "next_best_action": rec}


@app.post("/api/v1/migrations/jobs", dependencies=[Depends(require_role("admin", "operator"))])
def create_migration_job(payload: MigrationJobRequest) -> dict:
    job_id = enqueue("migration_create", _create_migration_job_task, payload)
    return {"queue_job_id": job_id, "status": "queued"}


def _create_migration_job_task(payload: MigrationJobRequest) -> dict:
    with get_session() as session:
        job = MigrationJob(**payload.model_dump(), status="completed", progress_percent=100)
        session.add(job)
        _append_audit(session, "migration", "job_create", payload.model_dump_json())
        session.commit()
        session.refresh(job)
    return job.model_dump()


@app.patch("/api/v1/migrations/jobs/{job_id}", dependencies=[Depends(require_role("admin", "operator"))])
def update_migration_job(job_id: int, payload: MigrationJobUpdateRequest) -> dict:
    with get_session() as session:
        job = session.get(MigrationJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="migration job not found")
        updates = payload.model_dump(exclude_none=True)
        for key, value in updates.items():
            setattr(job, key, value)
        session.add(job)
        _append_audit(session, "migration", "job_update", f"{job_id}:{updates}")
        session.commit()
        session.refresh(job)
    return job.model_dump()


@app.post("/api/v1/migrations/jobs/{job_id}/complete", dependencies=[Depends(require_role("admin", "operator"))])
def complete_migration_job(job_id: int) -> dict:
    with get_session() as session:
        job = session.get(MigrationJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="migration job not found")
        job.status = "completed"
        job.progress_percent = 100
        session.add(job)
        session.commit()
    return {"job_id": job_id, "status": "completed"}


@app.post("/api/v1/sftp/endpoints", dependencies=[Depends(require_role("admin", "operator"))])
def create_sftp_endpoint(payload: SFTPEndpointRequest) -> dict:
    with get_session() as session:
        endpoint = SFTPEndpoint(tenant_id=payload.tenant_id, host=payload.host, key_fingerprint=payload.key_fingerprint, policy_json=payload.policy_json, expires_at=datetime.fromisoformat(payload.expires_at))
        session.add(endpoint)
        _append_audit(session, "migration", "sftp_create", payload.model_dump_json())
        session.commit()
        session.refresh(endpoint)
    return endpoint.model_dump()


@app.post("/api/v1/mobile/devices", dependencies=[Depends(require_role("admin", "operator"))])
def register_mobile_device(payload: MobileDeviceRequest) -> dict:
    with get_session() as session:
        mobile = MobileDevice(**payload.model_dump(), compliance_status="unknown")
        session.add(mobile)
        _append_audit(session, "mobile", "device_register", payload.model_dump_json())
        session.commit()
        session.refresh(mobile)
    return mobile.model_dump()


@app.post("/api/v1/mobile/assessments", dependencies=[Depends(require_role("admin", "operator"))])
def create_mobile_assessment(payload: MobileAssessmentRequest) -> dict:
    with get_session() as session:
        device = session.get(MobileDevice, payload.mobile_device_id)
        if not device:
            raise HTTPException(status_code=404, detail="mobile device not found")
        assessment = MobileAssessment(mobile_device_id=payload.mobile_device_id, check_profile=payload.check_profile, findings=payload.findings, risk=payload.risk, actions=payload.actions)
        session.add(assessment)
        sha, signature = sign_like(payload.findings + payload.actions)
        session.commit()
        session.refresh(assessment)
        report = MobileReport(mobile_assessment_id=assessment.id, pdf_path=f"/reports/mobile_{assessment.id}.pdf", sha256=sha, signature=signature, technician=payload.technician)
        session.add(report)
        _append_audit(session, payload.technician, "mobile_assessment", payload.model_dump_json())
        session.commit()
        session.refresh(report)
    return {"assessment_id": assessment.id, "report_id": report.id}


@app.post("/api/v1/workshop/iso/build", dependencies=[Depends(require_role("admin", "operator"))])
def build_workshop_iso(payload: ISOBuildRequest) -> dict:
    job_id = enqueue("iso_build", _build_workshop_iso_task, payload)
    return {"queue_job_id": job_id, "status": "queued"}


def _build_workshop_iso_task(payload: ISOBuildRequest) -> dict:
    iso_dir = Path("./artifacts/iso")
    iso_dir.mkdir(parents=True, exist_ok=True)
    safe_profile = payload.profile.replace("/", "-")
    file_name = f"niscore-{safe_profile}.iso"
    iso_path = iso_dir / file_name
    manifest = iso_dir / f"{safe_profile}.manifest.txt"
    toolkit_dir = iso_dir / f"{safe_profile}_usb_toolkit"
    toolkit_dir.mkdir(parents=True, exist_ok=True)

    connect_script = toolkit_dir / "connect_and_report.sh"
    connect_script.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
CONTROLLER_URL="{payload.controller_url.rstrip('/')}"
LIVE_TOKEN=${{NISCORE_LIVE_TOKEN:-}}
ASSET_ID=${{1:-unknown-asset}}
if [[ -z "${{LIVE_TOKEN}}" ]]; then
  echo 'NISCORE_LIVE_TOKEN fehlt' >&2
  exit 1
fi
HOSTNAME=$(hostname)
curl -fsS -X POST "${{CONTROLLER_URL}}/api/v1/live/status" \
  -H "X-Live-Token: ${{LIVE_TOKEN}}" \
  -H 'Content-Type: application/json' \
  -d "{{\"asset_id\":\"${{ASSET_ID}}\",\"source\":\"usb-toolkit\",\"stage\":\"boot\",\"status\":\"running\",\"progress_percent\":10,\"details\":\"host=${{HOSTNAME}}\"}}"
echo 'Status gemeldet.'
"""
    )
    connect_script.chmod(0o755)

    readme = toolkit_dir / "README.txt"
    readme.write_text(
        "NISCore USB Toolkit\n"
        "1) Live-System booten\n"
        "2) NISCORE_LIVE_TOKEN setzen\n"
        "3) ./connect_and_report.sh <asset-id> ausführen\n"
        "4) Optional: lokale Diagnose-/Wipe-Tools ergänzen\n"
    )

    manifest.write_text(
        "\n".join(
            [
                f"profile={payload.profile}",
                f"base_distribution={payload.base_distribution}",
                f"include_tools={','.join(payload.include_tools)}",
                f"controller_url={payload.controller_url}",
                f"auto_connect={payload.auto_connect}",
                f"toolkit_path={toolkit_dir}",
                "mode=mvp-usb-toolkit",
            ]
        )
    )

    iso_path.write_bytes(b"NISCORE-ISO-PLACEHOLDER")

    with get_session() as session:
        _append_audit(session, "system", "iso_build", payload.model_dump_json())
        session.commit()
    return {
        "status": "created",
        "iso_path": str(iso_path),
        "manifest_path": str(manifest),
        "toolkit_path": str(toolkit_dir),
        "connect_script": str(connect_script),
    }


@app.post("/api/v1/integrations/github/ssh-key", dependencies=[Depends(require_role("admin", "operator"))])
def store_github_ssh_key(payload: GitHubSSHKeyRequest) -> dict:
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(ssh_dir, 0o700)

    key_file = ssh_dir / "id_ed25519.pub"
    key_file.write_text(payload.public_key.strip() + "\n")
    os.chmod(key_file, 0o644)

    config_file = ssh_dir / "config"
    cfg = "Host github.com\n  HostName github.com\n  User git\n  IdentityFile ~/.ssh/id_ed25519\n  IdentitiesOnly yes\n"
    if not config_file.exists() or "Host github.com" not in config_file.read_text():
        with config_file.open("a") as f:
            f.write("\n" + cfg)
        os.chmod(config_file, 0o600)

    with get_session() as session:
        _append_audit(session, "system", "github_ssh_key_store", f"title={payload.title}")
        session.commit()

    return {
        "stored": True,
        "title": payload.title,
        "public_key_path": str(key_file),
        "hint": "private key id_ed25519 must also exist on host for git@github.com access",
    }


@app.get("/api/v1/jobs/{job_id}")
def get_queue_job(job_id: str, ctx: AuthContext = Depends(require_role("admin", "operator", "viewer"))) -> dict:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="queue job not found")
    return job.__dict__
@app.get("/api/v1/integrations/ndesk/assets")
def ndesk_list_assets(limit: int = 100) -> dict:
    safe_limit = 1 if limit < 1 else min(limit, 500)
    try:
        result = ndesk_request("GET", "/api/assets", params={"limit": safe_limit})
    except NdeskClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"source": "ndesk", "assets": result}


@app.post("/api/v1/integrations/ndesk/tickets")
def ndesk_create_ticket(payload: NdeskTicketCreateRequest) -> dict:
    body = payload.model_dump(exclude_none=True)
    try:
        created = ndesk_request("POST", "/api/tickets", payload=body)
    except NdeskClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    with get_session() as session:
        _append_audit(session, "ndesk", "ticket_create", payload.model_dump_json())
        session.commit()
    return {"source": "ndesk", "ticket": created}


@app.get("/api/v1/integrations/ndesk/users")
def ndesk_list_users(limit: int = 100) -> dict:
    safe_limit = 1 if limit < 1 else min(limit, 500)
    try:
        users = ndesk_request("GET", "/api/users", params={"limit": safe_limit})
    except NdeskClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"source": "ndesk", "users": users}


@app.post("/api/v1/integrations/ndesk/users")
def ndesk_create_user(payload: NdeskUserRequest) -> dict:
    body = payload.model_dump(exclude_none=True)
    try:
        created = ndesk_request("POST", "/api/users", payload=body)
    except NdeskClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    with get_session() as session:
        _append_audit(session, "ndesk", "user_create", payload.model_dump_json())
        session.commit()
    return {"source": "ndesk", "user": created}


@app.patch("/api/v1/integrations/ndesk/users/{user_id}")
def ndesk_update_user(user_id: str, payload: NdeskUserUpdateRequest) -> dict:
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="no updates provided")
    try:
        updated = ndesk_request("PATCH", f"/api/users/{user_id}", payload=updates)
    except NdeskClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    with get_session() as session:
        _append_audit(session, "ndesk", "user_update", f"{user_id}:{updates}")
        session.commit()
    return {"source": "ndesk", "user": updated}


@app.post("/api/v1/live/status", dependencies=[Depends(_require_live_token)])
async def push_live_status(payload: LiveStatusEventRequest) -> dict:
    safe_progress = max(0, min(100, payload.progress_percent))
    with get_session() as session:
        event = LiveStatusEvent(
            asset_id=payload.asset_id,
            source=payload.source,
            stage=payload.stage,
            status=payload.status,
            progress_percent=safe_progress,
            details=payload.details,
        )
        session.add(event)
        _append_audit(session, payload.source, "live_status_push", payload.model_dump_json())
        session.commit()
        session.refresh(event)

    body = jsonable_encoder(event)
    await live_status_hub.broadcast(body)
    return {"stored": True, "event_id": event.id}


@app.get("/api/v1/live/status", dependencies=[Depends(_require_live_token)])
def list_live_status(limit: int = 100) -> list[dict]:
    safe_limit = 1 if limit < 1 else min(limit, 500)
    with get_session() as session:
        events = session.exec(select(LiveStatusEvent).order_by(LiveStatusEvent.id.desc()).limit(safe_limit)).all()
    return [event.model_dump() for event in events]


@app.websocket("/ws/live/status")
async def live_status_websocket(websocket: WebSocket):
    expected = os.getenv("NISCORE_LIVE_TOKEN", "").strip()
    token = websocket.query_params.get("token", "")
    if not expected or not secure_equals(token, expected):
        await websocket.close(code=1008)
        return

    await live_status_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        live_status_hub.disconnect(websocket)
