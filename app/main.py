from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
import os
from pathlib import Path
from fastapi.responses import HTMLResponse
from sqlmodel import select

from app.db import get_session, init_db
from app.models import (
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
)
from app.services import hash_chain, recommend_for_finding, sign_like, ssl_days_until_expiry

app = FastAPI(title="NISCore API", version="0.3.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


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
        <article class='card'><h3>Version</h3><div class='kpi'>v0.3.0</div></article>
      </div>
    </section>
  </main>
</body>
</html>
"""


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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


@app.post("/api/v1/clients/register")
def register_client(payload: ClientRegisterRequest) -> dict:
    with get_session() as session:
        asset = Asset(**payload.model_dump(), status="registered")
        session.add(asset)
        _append_audit(session, "system", "client_register", payload.model_dump_json())
        session.commit()
        session.refresh(asset)
    return {"id": asset.id, "asset_id": asset.asset_id}


@app.patch("/api/v1/clients/{asset_id}")
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


@app.post("/api/v1/diagnostics/results")
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


@app.post("/api/v1/wipe/jobs")
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
        wipe_run_id = run.id
        session.commit()
        session.refresh(cert)
    return {"wipe_run_id": wipe_run_id, "certificate_id": cert.id, "sha256": cert.sha256}


@app.get("/api/v1/wipe/certificates/{certificate_id}")
def get_certificate(certificate_id: int) -> dict:
    with get_session() as session:
        cert = session.get(Certificate, certificate_id)
        if not cert:
            raise HTTPException(status_code=404, detail="certificate not found")
    return cert.model_dump()


@app.post("/api/v1/webhooks/test")
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


@app.post("/api/v1/security/endpoint-check")
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


@app.post("/api/v1/servers/health-check")
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


@app.post("/api/v1/migrations/jobs")
def create_migration_job(payload: MigrationJobRequest) -> dict:
    with get_session() as session:
        job = MigrationJob(**payload.model_dump(), status="running", progress_percent=10)
        session.add(job)
        _append_audit(session, "migration", "job_create", payload.model_dump_json())
        session.commit()
        session.refresh(job)
    return job.model_dump()


@app.patch("/api/v1/migrations/jobs/{job_id}")
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


@app.post("/api/v1/migrations/jobs/{job_id}/complete")
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


@app.post("/api/v1/sftp/endpoints")
def create_sftp_endpoint(payload: SFTPEndpointRequest) -> dict:
    with get_session() as session:
        endpoint = SFTPEndpoint(tenant_id=payload.tenant_id, host=payload.host, key_fingerprint=payload.key_fingerprint, policy_json=payload.policy_json, expires_at=datetime.fromisoformat(payload.expires_at))
        session.add(endpoint)
        _append_audit(session, "migration", "sftp_create", payload.model_dump_json())
        session.commit()
        session.refresh(endpoint)
    return endpoint.model_dump()


@app.post("/api/v1/mobile/devices")
def register_mobile_device(payload: MobileDeviceRequest) -> dict:
    with get_session() as session:
        mobile = MobileDevice(**payload.model_dump(), compliance_status="unknown")
        session.add(mobile)
        _append_audit(session, "mobile", "device_register", payload.model_dump_json())
        session.commit()
        session.refresh(mobile)
    return mobile.model_dump()


@app.post("/api/v1/mobile/assessments")
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
        assessment_id = assessment.id
        session.commit()
        session.refresh(report)
    return {"assessment_id": assessment_id, "report_id": report.id}


@app.post("/api/v1/workshop/iso/build")
def build_workshop_iso(payload: ISOBuildRequest) -> dict:
    iso_dir = Path("./artifacts/iso")
    iso_dir.mkdir(parents=True, exist_ok=True)
    safe_profile = payload.profile.replace("/", "-")
    file_name = f"niscore-{safe_profile}.iso"
    iso_path = iso_dir / file_name
    manifest = iso_dir / f"{safe_profile}.manifest.txt"
    manifest.write_text(
        "\n".join([
            f"profile={payload.profile}",
            f"base_distribution={payload.base_distribution}",
            f"include_tools={','.join(payload.include_tools)}",
            "note=placeholder image, integrate live-build pipeline for production",
        ])
    )
    iso_path.write_bytes(b"NISCORE-ISO-PLACEHOLDER")

    with get_session() as session:
        _append_audit(session, "system", "iso_build", payload.model_dump_json())
        session.commit()

    return {
        "status": "created",
        "iso_path": str(iso_path),
        "manifest_path": str(manifest),
        "next_step": "replace placeholder with live-build pipeline worker",
    }


@app.post("/api/v1/integrations/github/ssh-key")
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
