from __future__ import annotations

import json
import tarfile
import zipfile
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
    AgentSession,
    OperationRun,
    OperationTicketLink,
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
    WipeExecutionJob,
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
    WipeExecutionApprovalRequest,
    WipeExecutionCancelRequest,
    WipeExecutionRejectRequest,
    WipeAgentBuildRequest,
    WipeExecutionJobRequest,
    NdeskTicketCreateRequest,
    NdeskUserRequest,
    NdeskUserUpdateRequest,
    NdeskTicketEventRequest,
    LiveStatusEventRequest,
    StorageDetectRequest,
    StorageWipeRequest,
    LoginRequest,
    MissionRunRequest,
    AgentEnrollRequest,
    AgentHeartbeatRequest,
    OperationModuleRunRequest,
    OperationControlRequest,
    OperationTicketLinkRequest,
    OfflineBundleRequest,
)
from app.services import (
    NdeskClientError,
    hash_chain,
    ndesk_request,
    recommend_for_finding,
    detect_storage_devices,
    build_device_fingerprint,
    execute_module_logic,
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
MODULE_BLUEPRINTS = {
    "migration": {"stages": ["discovery", "mapping", "copy", "delta", "validation"], "default_progress": 10},
    "wipe": {"stages": ["detect", "approval", "dispatch", "wipe", "certificate"], "default_progress": 15},
    "hardware": {"stages": ["inventory", "diagnostics", "report"], "default_progress": 20},
    "seo": {"stages": ["crawl", "analyze", "report"], "default_progress": 15},
    "pentest": {"stages": ["scope", "recon", "verify", "report"], "default_progress": 10},
    "backup": {"stages": ["snapshot", "transfer", "verify"], "default_progress": 10},
    "mobile": {"stages": ["inventory", "assessment", "recommendation"], "default_progress": 20},
}
MODULE_EXECUTION_PROFILES = {
    "migration": {"required_parameters": ["source", "target"], "evidence": ["mapping_report", "delta_sync_log", "cutover_report"]},
    "wipe": {"required_parameters": ["serial_number", "storage_type"], "evidence": ["profile_used", "command_log", "certificate_ref"]},
    "hardware": {"required_parameters": ["collector"], "evidence": ["inventory_snapshot", "diagnostic_profile", "health_summary"]},
    "seo": {"required_parameters": ["target_url"], "evidence": ["crawl_report", "metrics_scorecard"]},
    "pentest": {"required_parameters": ["scope"], "evidence": ["scope_guardrail_log", "recon_summary", "validation_report"]},
    "backup": {"required_parameters": ["policy"], "evidence": ["backup_job_log", "verify_report", "retention_status"]},
    "mobile": {"required_parameters": ["check_profile"], "evidence": ["inventory_report", "assessment_report"]},
}


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


@app.post("/api/v1/agents/enroll", dependencies=[Depends(require_role("admin", "operator"))])
def enroll_agent(payload: AgentEnrollRequest) -> dict:
    expected = os.getenv("NISCORE_API_TOKEN", "").strip()
    if not expected or not secure_equals(payload.token, expected):
        raise HTTPException(status_code=401, detail="invalid enrollment token")
    with get_session() as session:
        current = session.exec(select(AgentSession).where(AgentSession.agent_id == payload.agent_id)).first()
        if current:
            current.asset_id = payload.asset_id
            current.platform = payload.platform
            current.mode = payload.mode
            current.status = "online"
            current.last_seen_at = datetime.utcnow()
            agent = current
        else:
            agent = AgentSession(
                agent_id=payload.agent_id,
                asset_id=payload.asset_id,
                platform=payload.platform,
                mode=payload.mode,
            )
        session.add(agent)
        _append_audit(session, "agent", "agent_enroll", payload.model_dump_json())
        session.commit()
        session.refresh(agent)
    return {"agent_session_id": agent.id, "agent_id": agent.agent_id, "status": agent.status}


@app.post("/api/v1/agents/{agent_id}/heartbeat", dependencies=[Depends(require_role("admin", "operator"))])
def heartbeat_agent(agent_id: str, payload: AgentHeartbeatRequest) -> dict:
    lease = 30 if payload.lease_seconds < 30 else min(payload.lease_seconds, 900)
    with get_session() as session:
        agent = session.exec(select(AgentSession).where(AgentSession.agent_id == agent_id)).first()
        if not agent:
            raise HTTPException(status_code=404, detail="agent session not found")
        agent.status = payload.status
        agent.last_seen_at = datetime.utcnow()
        session.add(agent)
        _append_audit(session, agent_id, "agent_heartbeat", payload.model_dump_json())
        session.commit()
    return {"agent_id": agent_id, "status": payload.status, "lease_seconds": lease, "next_heartbeat_until": datetime.utcnow().isoformat()}


@app.post("/api/v1/modules/run", dependencies=[Depends(require_role("admin", "operator"))])
def run_module(payload: OperationModuleRunRequest) -> dict:
    blueprint = MODULE_BLUEPRINTS[payload.module]
    profile = MODULE_EXECUTION_PROFILES[payload.module]
    missing = [key for key in profile["required_parameters"] if key not in payload.parameters]
    if missing:
        raise HTTPException(status_code=400, detail=f"missing module parameters: {', '.join(missing)}")
    with get_session() as session:
        run = OperationRun(
            module=payload.module,
            tenant_id=payload.tenant_id,
            asset_id=payload.asset_id,
            operator=payload.operator,
            status="running",
            progress_percent=blueprint["default_progress"],
            parameters_json=json.dumps({"stages": blueprint["stages"], "required_parameters": profile["required_parameters"], **payload.parameters}),
            result_json=json.dumps({"evidence_expected": profile["evidence"], "events": []}),
        )
        session.add(run)
        session.flush()
        session.add(
            LiveStatusEvent(
                asset_id=payload.asset_id,
                source=f"module:{payload.module}",
                stage=blueprint["stages"][0],
                status="running",
                progress_percent=run.progress_percent,
                details=f"module {payload.module} started with stage {blueprint['stages'][0]}",
            )
        )
        _append_audit(session, payload.operator, "module_run_create", payload.model_dump_json())
        session.commit()
        session.refresh(run)
    return {"run_id": run.id, "module": run.module, "status": run.status, "progress_percent": run.progress_percent}


@app.get("/api/v1/modules/runs", dependencies=[Depends(require_role("admin", "operator", "viewer"))])
def list_module_runs(limit: int = 50, offset: int = 0, module: str | None = None, status: str | None = None) -> list[dict]:
    limit = 1 if limit < 1 else min(limit, 500)
    offset = 0 if offset < 0 else offset
    with get_session() as session:
        query = select(OperationRun).order_by(OperationRun.id.desc())
        if module:
            query = query.where(OperationRun.module == module)
        if status:
            query = query.where(OperationRun.status == status)
        rows = session.exec(query.offset(offset).limit(limit)).all()
    return [r.model_dump() for r in rows]


@app.post("/api/v1/modules/{run_id}/progress", dependencies=[Depends(require_role("admin", "operator"))])
def update_module_progress(run_id: int, payload: LiveStatusEventRequest) -> dict:
    safe_progress = max(0, min(100, payload.progress_percent))
    with get_session() as session:
        run = session.get(OperationRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="operation run not found")
        if run.asset_id != payload.asset_id:
            raise HTTPException(status_code=400, detail="asset mismatch for operation run")
        run.progress_percent = safe_progress
        if safe_progress >= 100 and payload.status == "completed":
            run.status = "completed"
            run.result_json = json.dumps({"stage": payload.stage, "details": payload.details})
        session.add(run)
        event = LiveStatusEvent(
            asset_id=payload.asset_id,
            source=f"module:{run.module}",
            stage=payload.stage,
            status=payload.status,
            progress_percent=safe_progress,
            details=payload.details,
        )
        session.add(event)
        _append_audit(session, payload.source, "module_run_progress", f"{run_id}:{payload.model_dump_json()}")
        session.commit()
        session.refresh(run)
        session.refresh(event)
    return {"run_id": run.id, "status": run.status, "progress_percent": run.progress_percent, "event_id": event.id}


@app.post("/api/v1/modules/{run_id}/control", dependencies=[Depends(require_role("admin", "operator"))])
def control_module_run(run_id: int, payload: OperationControlRequest) -> dict:
    status_map = {"pause": "paused", "resume": "running", "cancel": "canceled", "approve": "approved", "reject": "rejected"}
    with get_session() as session:
        run = session.get(OperationRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="operation run not found")
        run.status = status_map[payload.action]
        session.add(run)
        session.add(
            LiveStatusEvent(
                asset_id=run.asset_id,
                source=f"module:{run.module}",
                stage="control",
                status=run.status,
                progress_percent=run.progress_percent,
                details=f"{payload.action} by {payload.actor}: {payload.note}",
            )
        )
        _append_audit(session, payload.actor, "module_run_control", f"{run_id}:{payload.model_dump_json()}")
        session.commit()
        session.refresh(run)
    return run.model_dump()


@app.post("/api/v1/modules/{run_id}/execute", dependencies=[Depends(require_role("admin", "operator"))])
def execute_module_run(run_id: int, actor: str = "system") -> dict:
    with get_session() as session:
        run = session.get(OperationRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="operation run not found")
        params = json.loads(run.parameters_json) if run.parameters_json else {}
        execution = execute_module_logic(run.module, params)
        run.status = "completed"
        run.progress_percent = 100
        run.result_json = json.dumps(
            {
                "executed_at": datetime.utcnow().isoformat(),
                "module": run.module,
                "execution": execution,
            }
        )
        session.add(run)
        session.add(
            LiveStatusEvent(
                asset_id=run.asset_id,
                source=f"module:{run.module}",
                stage="execution",
                status="completed",
                progress_percent=100,
                details=execution.get("summary", "module execution completed"),
            )
        )
        _append_audit(session, actor, "module_run_execute", f"run_id={run_id};module={run.module}")
        session.commit()
        session.refresh(run)
    return {"run_id": run.id, "status": run.status, "progress_percent": run.progress_percent, "result": json.loads(run.result_json)}


@app.post("/api/v1/modules/{run_id}/tickets/link", dependencies=[Depends(require_role("admin", "operator"))])
def link_module_ticket(run_id: int, payload: OperationTicketLinkRequest) -> dict:
    with get_session() as session:
        run = session.get(OperationRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="operation run not found")
        existing = session.exec(
            select(OperationTicketLink).where(
                OperationTicketLink.operation_run_id == run_id,
                OperationTicketLink.ndesk_ticket_id == payload.ticket_id,
            )
        ).first()
        if existing:
            return {"linked": True, "link_id": existing.id, "operation_run_id": run_id, "ticket_id": payload.ticket_id}
        link = OperationTicketLink(
            operation_run_id=run_id,
            ndesk_ticket_id=payload.ticket_id,
            relation=payload.relation,
        )
        session.add(link)
        _append_audit(session, payload.actor, "module_ticket_link", f"{run_id}:{payload.model_dump_json()}")
        session.commit()
        session.refresh(link)
    return {"linked": True, "link_id": link.id, "operation_run_id": run_id, "ticket_id": payload.ticket_id}


@app.get("/api/v1/modules/{run_id}/tickets", dependencies=[Depends(require_role("admin", "operator", "viewer"))])
def list_module_tickets(run_id: int) -> list[dict]:
    with get_session() as session:
        rows = session.exec(select(OperationTicketLink).where(OperationTicketLink.operation_run_id == run_id)).all()
    return [r.model_dump() for r in rows]


@app.post("/api/v1/modules/offline/bundle", dependencies=[Depends(require_role("admin", "operator"))])
def build_offline_bundle(payload: OfflineBundleRequest) -> dict:
    with get_session() as session:
        run = session.get(OperationRun, payload.run_id)
        if not run:
            raise HTTPException(status_code=404, detail="operation run not found")
        bundle_dir = Path("./artifacts/offline-bundles")
        bundle_dir.mkdir(parents=True, exist_ok=True)
        out_file = bundle_dir / f"offline-run-{run.id}.json"
        bundle_payload = {
            "run_id": run.id,
            "module": run.module,
            "asset_id": run.asset_id,
            "profile": payload.profile,
            "include_tasks": payload.include_tasks,
            "parameters": json.loads(run.parameters_json),
            "generated_at": datetime.utcnow().isoformat(),
        }
        out_file.write_text(json.dumps(bundle_payload, indent=2))
        bundle_sha, bundle_sig = sign_like(json.dumps(bundle_payload, sort_keys=True))
        sig_file = bundle_dir / f"offline-run-{run.id}.sig"
        sha_file = bundle_dir / f"offline-run-{run.id}.sha256"
        sig_file.write_text(bundle_sig + "\n")
        sha_file.write_text(bundle_sha + "\n")
        _append_audit(
            session,
            payload.created_by,
            "offline_bundle_build",
            f"run_id={run.id};file={out_file};sha256={bundle_sha};sig={bundle_sig}",
        )
        session.commit()
        run_id = run.id
    return {
        "created": True,
        "run_id": run_id,
        "bundle_path": str(out_file),
        "bundle_sha256_path": str(sha_file),
        "bundle_signature_path": str(sig_file),
        "bundle_sha256": bundle_sha,
    }


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


@app.post("/api/v1/missions/run", dependencies=[Depends(require_role("admin", "operator"))])
def run_mission(payload: MissionRunRequest) -> dict:
    with get_session() as session:
        asset = session.exec(select(Asset).where(Asset.asset_id == payload.asset_id)).first()
        if not asset:
            asset = Asset(
                tenant_id=payload.tenant_id,
                asset_id=payload.asset_id,
                serial_number=payload.serial_number,
                device_type=payload.device_type,
                status="registered",
            )
            session.add(asset)
            session.flush()
            _append_audit(session, "system", "client_register", payload.model_dump_json())
        else:
            asset.serial_number = payload.serial_number
            asset.device_type = payload.device_type
            session.add(asset)
            _append_audit(session, "system", "client_update", payload.model_dump_json())

        run = DiagnosticRun(asset_id=asset.id, technician=payload.technician, result=payload.finding, raw_json='{"source":"mission-control"}')
        session.add(run)
        rec = _create_recommendation(session, payload.finding, 'mission-control')
        _append_audit(session, payload.technician, "diagnostic_upload", payload.model_dump_json())

        wipe_result = None
        if payload.with_wipe:
            wipe_run = WipeRun(
                asset_id=asset.id,
                method=payload.wipe_method,
                standard=payload.wipe_standard,
                status="completed",
                command_log=f"wipe {payload.wipe_method} {payload.wipe_standard}",
                device_fingerprint=f"{asset.asset_id}:{asset.serial_number}",
            )
            session.add(wipe_run)
            session.flush()
            sha, signature = sign_like(f"{asset.asset_id}:{wipe_run.id}:{wipe_run.command_log}")
            cert = Certificate(wipe_run_id=wipe_run.id, sha256=sha, signature=signature, pdf_path=f"/certs/wipe_{wipe_run.id}.pdf")
            session.add(cert)
            _append_audit(session, payload.technician, "wipe_run", payload.model_dump_json())
            wipe_result = {"wipe_run_id": wipe_run.id, "certificate_id": cert.id, "sha256": cert.sha256}

        session.commit()
        session.refresh(run)
        session.refresh(rec)

    return {
        "asset_id": payload.asset_id,
        "diagnostic_run_id": run.id,
        "recommendation": rec.model_dump(),
        "wipe": wipe_result,
    }


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


@app.post("/api/v1/wipe/execution-jobs", dependencies=[Depends(require_role("admin", "operator"))])
def create_wipe_execution_job(payload: WipeExecutionJobRequest) -> dict:
    with get_session() as session:
        asset = session.exec(select(Asset).where(Asset.asset_id == payload.asset_id)).first()
        if not asset:
            raise HTTPException(status_code=404, detail="asset not found")
        job = WipeExecutionJob(
            asset_id=asset.id,
            target_serial=payload.serial_number,
            storage_type=payload.storage_type,
            execution_mode=payload.execution_mode,
            standard_profile=payload.standard_profile,
            status="pending_approval",
            created_by=payload.created_by,
            device_fingerprint=build_device_fingerprint(payload.asset_id, payload.serial_number, payload.execution_mode, payload.standard_profile),
        )
        session.add(job)
        _append_audit(session, payload.created_by, "wipe_execution_job_created", payload.model_dump_json())
        session.commit()
        session.refresh(job)
    return {"execution_job_id": job.id, "status": job.status}


@app.post("/api/v1/wipe/execution-jobs/{job_id}/approve", dependencies=[Depends(require_role("admin"))])
def approve_wipe_execution_job(job_id: int, payload: WipeExecutionApprovalRequest) -> dict:
    with get_session() as session:
        job = session.get(WipeExecutionJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="wipe execution job not found")
        if job.status != "pending_approval":
            raise HTTPException(status_code=400, detail="job is not pending approval")
        if payload.approved_by == job.created_by:
            raise HTTPException(status_code=400, detail="four-eyes principle violated")
        job.approved_by = payload.approved_by
        job.approval_note = payload.approval_note
        job.status = "approved"
        session.add(job)
        _append_audit(session, payload.approved_by, "wipe_execution_job_approved", f"{job_id}:{payload.approval_note}")
        session.commit()
    return {"execution_job_id": job_id, "status": "approved", "approved_by": payload.approved_by}


@app.post("/api/v1/wipe/execution-jobs/{job_id}/dispatch", dependencies=[Depends(require_role("admin", "operator"))])
def dispatch_wipe_execution_job(job_id: int) -> dict:
    with get_session() as session:
        job = session.get(WipeExecutionJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="wipe execution job not found")
        if job.status not in {"approved", "dispatched_agent", "dispatched_boot"}:
            raise HTTPException(status_code=400, detail="job must be approved before dispatch")
        if job.status in {"dispatched_agent", "dispatched_boot"}:
            return {"execution_job_id": job_id, "status": job.status, "execution_mode": job.execution_mode}
        job.status = "dispatched_boot" if job.execution_mode == "boot" else "dispatched_agent"
        status = job.status
        execution_mode = job.execution_mode
        session.add(job)
        _append_audit(session, "orchestrator", "wipe_execution_job_dispatched", str(job_id))
        session.commit()
    return {"execution_job_id": job_id, "status": status, "execution_mode": execution_mode}


@app.get("/api/v1/wipe/execution-jobs", dependencies=[Depends(require_role("admin", "operator", "viewer"))])
def list_wipe_execution_jobs(limit: int = 50) -> list[dict]:
    limit = 1 if limit < 1 else min(limit, 500)
    with get_session() as session:
        entries = session.exec(select(WipeExecutionJob).order_by(WipeExecutionJob.id.desc()).limit(limit)).all()
    return [e.model_dump() for e in entries]


@app.post("/api/v1/wipe/execution-jobs/{job_id}/agent/build", dependencies=[Depends(require_role("admin", "operator"))])
def build_wipe_agent(job_id: int, payload: WipeAgentBuildRequest) -> dict:
    if payload.execution_job_id != job_id:
        raise HTTPException(status_code=400, detail="job id mismatch")
    with get_session() as session:
        job = session.get(WipeExecutionJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="wipe execution job not found")
        if job.status not in {"approved", "dispatched_agent", "dispatched_boot"}:
            raise HTTPException(status_code=400, detail="wipe execution job is not approved")
    job_ref = enqueue("wipe_agent_build", _build_wipe_agent_task, payload)
    return {"queue_job_id": job_ref, "status": "queued"}


@app.post("/api/v1/wipe/execution-jobs/{job_id}/reject", dependencies=[Depends(require_role("admin"))])
def reject_wipe_execution_job(job_id: int, payload: WipeExecutionRejectRequest) -> dict:
    with get_session() as session:
        job = session.get(WipeExecutionJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="wipe execution job not found")
        if job.status != "pending_approval":
            raise HTTPException(status_code=400, detail="job can only be rejected from pending_approval")
        job.status = "rejected"
        job.rejected_by = payload.rejected_by
        job.rejection_note = payload.rejection_note
        session.add(job)
        _append_audit(session, payload.rejected_by, "wipe_execution_job_rejected", f"{job_id}:{payload.rejection_note}")
        session.commit()
    return {"execution_job_id": job_id, "status": "rejected", "rejected_by": payload.rejected_by}


@app.post("/api/v1/wipe/execution-jobs/{job_id}/cancel", dependencies=[Depends(require_role("admin", "operator"))])
def cancel_wipe_execution_job(job_id: int, payload: WipeExecutionCancelRequest) -> dict:
    with get_session() as session:
        job = session.get(WipeExecutionJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="wipe execution job not found")
        if job.status in {"completed", "canceled"}:
            raise HTTPException(status_code=400, detail="job can not be canceled from current state")
        job.status = "canceled"
        job.canceled_by = payload.canceled_by
        job.cancel_note = payload.cancel_note
        session.add(job)
        _append_audit(session, payload.canceled_by, "wipe_execution_job_canceled", f"{job_id}:{payload.cancel_note}")
        session.commit()
    return {"execution_job_id": job_id, "status": "canceled", "canceled_by": payload.canceled_by}


def _build_wipe_agent_task(payload: WipeAgentBuildRequest) -> dict:
    with get_session() as session:
        job = session.get(WipeExecutionJob, payload.execution_job_id)
        if not job:
            raise RuntimeError("wipe execution job not found")
        if job.status not in {"approved", "dispatched_agent", "dispatched_boot"}:
            raise RuntimeError("wipe execution job is not approved")
        asset = session.get(Asset, job.asset_id)
        if not asset:
            raise RuntimeError("asset for wipe execution job not found")

        agent_dir = Path("./artifacts/agents")
        agent_dir.mkdir(parents=True, exist_ok=True)
        package_dir = agent_dir / f"wipe-agent-job-{job.id}"
        package_dir.mkdir(parents=True, exist_ok=True)

        config_json = package_dir / "agent_config.json"
        config_json.write_text(
            json.dumps(
                jsonable_encoder(
                    {
                        "execution_job_id": job.id,
                        "asset_id": asset.asset_id,
                        "target_serial": job.target_serial,
                        "storage_type": job.storage_type,
                        "execution_mode": job.execution_mode,
                        "standard_profile": job.standard_profile,
                        "approved_by": job.approved_by,
                        "device_fingerprint": job.device_fingerprint,
                        "os_target": payload.os_target,
                    }
                ),
                indent=2,
            )
        )

        runner = package_dir / "run_wipe_agent.sh"
        runner.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
CFG_FILE=${1:-agent_config.json}
if [[ ! -f "$CFG_FILE" ]]; then
  echo "agent config not found: $CFG_FILE" >&2
  exit 1
fi
echo "Starting wipe agent with config: $CFG_FILE"
cat "$CFG_FILE"
echo "MVP mode: orchestration-only runner. Integrate native wipe binary here."
"""
        )
        runner.chmod(0o755)

        readme = package_dir / "README.txt"
        readme.write_text(
            "NISCore Wipe Agent Package\n"
            "- Entpacken auf Zielsystem\n"
            "- agent_config.json prüfen (Job/Serial/Fingerprint)\n"
            "- ./run_wipe_agent.sh ausführen\n"
            "- Für produktiv: native wipe engine + signed reporting ergänzen\n"
        )

        package_path = str(package_dir)
        artifact_path = None
        if payload.output_format == "tar.gz":
            tar_path = agent_dir / f"wipe-agent-job-{job.id}.tar.gz"
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(package_dir, arcname=package_dir.name)
            artifact_path = str(tar_path)
        elif payload.output_format == "zip":
            zip_path = agent_dir / f"wipe-agent-job-{job.id}.zip"
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for f in package_dir.rglob("*"):
                    zf.write(f, arcname=f.relative_to(package_dir.parent))
            artifact_path = str(zip_path)

        manifest_data = json.dumps(
            {
                "job_id": job.id,
                "asset_id": asset.asset_id,
                "status": job.status,
                "output_format": payload.output_format,
                "artifact_path": artifact_path,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        manifest_sha, manifest_sig = sign_like(manifest_data)
        (package_dir / "manifest.json").write_text(manifest_data)
        (package_dir / "manifest.sha256").write_text(manifest_sha + "\n")
        (package_dir / "manifest.sig").write_text(manifest_sig + "\n")

        _append_audit(session, "orchestrator", "wipe_agent_generated", f"job_id={job.id};os={payload.os_target}")
        session.commit()
    return {
        "status": "created",
        "package_path": package_path,
        "config_path": str(config_json),
        "runner_path": str(runner),
        "artifact_path": artifact_path,
        "output_format": payload.output_format,
    }
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


@app.post("/api/v1/integrations/ndesk/staff-sync")
def ndesk_staff_sync(limit: int = 100) -> dict:
    safe_limit = 1 if limit < 1 else min(limit, 1000)
    try:
        users = ndesk_request("GET", "/api/users", params={"limit": safe_limit})
    except NdeskClientError as exc:
        raise HTTPException(status_code=502, detail=f"ndesk error: {exc}") from exc
    with get_session() as session:
        _append_audit(session, "ndesk", "staff_sync", f"count={len(users) if isinstance(users, list) else 'unknown'}")
        session.commit()
    return {"source": "ndesk", "synced": users}


@app.get("/api/v1/integrations/ndesk/tickets")
def ndesk_list_tickets(limit: int = 100) -> dict:
    safe_limit = 1 if limit < 1 else min(limit, 1000)
    try:
        tickets = ndesk_request("GET", "/api/tickets", params={"limit": safe_limit})
    except NdeskClientError as exc:
        raise HTTPException(status_code=502, detail=f"ndesk error: {exc}") from exc
    with get_session() as session:
        _append_audit(session, "ndesk", "ticket_sync_pull", f"count={len(tickets) if isinstance(tickets, list) else 'unknown'}")
        session.commit()
    return {"source": "ndesk", "tickets": tickets}


@app.get("/api/v1/integrations/ndesk/tickets/sync", dependencies=[Depends(require_role("admin", "operator"))])
def ndesk_ticket_sync(limit: int = 100, cursor: str | None = None) -> dict:
    safe_limit = 1 if limit < 1 else min(limit, 1000)
    params: dict[str, str | int] = {"limit": safe_limit}
    if cursor:
        params["cursor"] = cursor
    try:
        raw = ndesk_request("GET", "/api/tickets", params=params)
    except NdeskClientError as exc:
        raise HTTPException(status_code=502, detail=f"ndesk error: {exc}") from exc

    tickets = raw if isinstance(raw, list) else raw.get("tickets", [])
    next_cursor = raw.get("next_cursor") if isinstance(raw, dict) else None
    linked_runs = 0
    with get_session() as session:
        for ticket in tickets if isinstance(tickets, list) else []:
            ticket_id = str(ticket.get("id") or ticket.get("ticket_id") or "")
            if not ticket_id:
                continue
            link = session.exec(select(OperationTicketLink).where(OperationTicketLink.ndesk_ticket_id == ticket_id)).first()
            if not link:
                continue
            run = session.get(OperationRun, link.operation_run_id)
            if not run:
                continue
            payload = {"ticket_id": ticket_id, "ticket_status": ticket.get("status", "unknown"), "synced_at": datetime.utcnow().isoformat()}
            run.result_json = json.dumps({"sync": payload, "previous": run.result_json})
            session.add(run)
            linked_runs += 1
        _append_audit(session, "ndesk", "ticket_sync_pull_incremental", f"count={len(tickets) if isinstance(tickets, list) else 0};cursor={cursor or '-'};linked_runs={linked_runs}")
        session.commit()
    return {"source": "ndesk", "tickets": tickets, "next_cursor": next_cursor, "linked_runs": linked_runs}


@app.post("/api/v1/integrations/ndesk/tickets/events", dependencies=[Depends(require_role("admin", "operator"))])
def ndesk_ticket_event(payload: NdeskTicketEventRequest) -> dict:
    with get_session() as session:
        run: OperationRun | None = None
        if payload.run_id is not None:
            run = session.get(OperationRun, payload.run_id)
        if not run:
            link = session.exec(select(OperationTicketLink).where(OperationTicketLink.ndesk_ticket_id == payload.ticket_id)).first()
            if link:
                run = session.get(OperationRun, link.operation_run_id)
        if not run:
            raise HTTPException(status_code=404, detail="no linked operation run for ticket event")

        normalized = payload.status.lower()
        status_map = {
            "open": "running",
            "in_progress": "running",
            "waiting": "paused",
            "resolved": "completed",
            "closed": "completed",
            "rejected": "rejected",
            "canceled": "canceled",
        }
        run.status = status_map.get(normalized, run.status)
        session.add(run)
        session.add(
            LiveStatusEvent(
                asset_id=run.asset_id,
                source="ndesk:webhook",
                stage="ticket_sync",
                status=run.status,
                progress_percent=run.progress_percent,
                details=f"ticket {payload.ticket_id} -> {payload.status}; note={payload.note}",
            )
        )
        _append_audit(session, payload.actor, "ndesk_ticket_event", payload.model_dump_json())
        session.commit()
        session.refresh(run)
    return {"mapped": True, "run_id": run.id, "run_status": run.status, "ticket_id": payload.ticket_id}


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
