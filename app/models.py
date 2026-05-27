from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(index=True, default="default")
    asset_id: str = Field(index=True, unique=True)
    serial_number: str
    device_type: str
    status: str = "new"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DiagnosticRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(index=True)
    technician: str
    result: str
    raw_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StorageDevice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(index=True)
    model: str
    serial_number: str
    health: str
    smart_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WipeRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(index=True)
    method: str
    standard: str
    status: str = "queued"
    command_log: str = ""
    device_fingerprint: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WipeExecutionJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(index=True)
    target_serial: str
    storage_type: str = "nvme"
    execution_mode: str = "agent"
    standard_profile: str = "nist-800-88"
    status: str = "pending_approval"
    created_by: str
    approved_by: Optional[str] = None
    approval_note: str = ""
    rejected_by: Optional[str] = None
    rejection_note: str = ""
    canceled_by: Optional[str] = None
    cancel_note: str = ""
    device_fingerprint: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Certificate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    wipe_run_id: int = Field(index=True)
    sha256: str
    signature: str
    pdf_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WebScan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target: str
    scan_type: str
    findings: str
    severity: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alert_type: str
    severity: str
    channel: str
    acknowledged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user: str
    action: str
    payload: str
    prev_hash: str
    current_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Recommendation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    finding_type: str
    priority: str
    action: str
    risk: str
    status: str = "open"
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MigrationJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(index=True)
    job_type: str
    source: str
    target: str
    status: str = "queued"
    progress_percent: int = 0
    error_rate: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MigrationItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    migration_job_id: int = Field(index=True)
    object_id: str
    path_or_message_id: str
    result: str
    error_code: str = ""
    retry_count: int = 0


class SFTPEndpoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(index=True)
    host: str
    key_fingerprint: str
    policy_json: str
    expires_at: datetime


class MobileDevice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(index=True)
    platform: str
    model: str
    serial_or_udid: str
    ownership: str
    compliance_status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MobileAssessment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mobile_device_id: int = Field(index=True)
    check_profile: str
    findings: str
    risk: str
    actions: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MobileReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mobile_assessment_id: int = Field(index=True)
    pdf_path: str
    sha256: str
    signature: str
    technician: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LiveStatusEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: str = Field(index=True)
    source: str
    stage: str
    status: str
    progress_percent: int = 0
    details: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(index=True, unique=True)
    asset_id: str = Field(index=True)
    platform: str
    mode: str = "agent"
    status: str = "online"
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)


class OperationRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    module: str = Field(index=True)
    tenant_id: str = Field(index=True, default="default")
    asset_id: str = Field(index=True)
    operator: str
    status: str = "queued"
    progress_percent: int = 0
    parameters_json: str = "{}"
    result_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OperationTicketLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    operation_run_id: int = Field(index=True)
    ndesk_ticket_id: str = Field(index=True)
    relation: str = "primary"
    created_at: datetime = Field(default_factory=datetime.utcnow)
