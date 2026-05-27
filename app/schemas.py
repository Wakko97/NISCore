from pydantic import BaseModel
from typing import Literal


class LoginRequest(BaseModel):
    username: str
    role: str
    password: str


class ClientRegisterRequest(BaseModel):
    tenant_id: str = "default"
    asset_id: str
    serial_number: str
    device_type: str


class ClientUpdateRequest(BaseModel):
    serial_number: str | None = None
    device_type: str | None = None
    status: str | None = None


class DiagnosticResultRequest(BaseModel):
    asset_id: str
    technician: str
    result: str
    raw_json: str


class WipeJobRequest(BaseModel):
    asset_id: str
    method: str
    standard: str


class WipeExecutionJobRequest(BaseModel):
    asset_id: str
    serial_number: str
    storage_type: Literal["hdd", "ssd", "nvme"] = "nvme"
    execution_mode: Literal["agent", "boot"] = "agent"
    standard_profile: Literal["nist-800-88", "ata-secure-erase", "nvme-sanitize"] = "nist-800-88"
    created_by: str


class WipeExecutionApprovalRequest(BaseModel):
    approved_by: str
    approval_note: str = ""


class WipeExecutionRejectRequest(BaseModel):
    rejected_by: str
    rejection_note: str


class WipeExecutionCancelRequest(BaseModel):
    canceled_by: str
    cancel_note: str = ""


class WipeAgentBuildRequest(BaseModel):
    execution_job_id: int
    os_target: Literal["linux", "windows"] = "linux"
    output_format: Literal["dir", "tar.gz", "zip"] = "tar.gz"


class WebhookTestRequest(BaseModel):
    channel: str
    payload: str


class SSLCheckRequest(BaseModel):
    host: str
    port: int = 443


class EndpointCheckRequest(BaseModel):
    asset_id: str
    scan_type: str
    details: str


class ServerHealthRequest(BaseModel):
    asset_id: str
    platform: str
    metrics_json: str


class AIAssistRequest(BaseModel):
    context: str
    finding_type: str
    details: str


class MigrationJobRequest(BaseModel):
    tenant_id: str
    job_type: str
    source: str
    target: str


class MigrationJobUpdateRequest(BaseModel):
    status: str | None = None
    progress_percent: int | None = None
    error_rate: float | None = None


class SFTPEndpointRequest(BaseModel):
    tenant_id: str
    host: str
    key_fingerprint: str
    policy_json: str
    expires_at: str


class MobileDeviceRequest(BaseModel):
    tenant_id: str
    platform: str
    model: str
    serial_or_udid: str
    ownership: str


class MobileAssessmentRequest(BaseModel):
    mobile_device_id: int
    check_profile: str
    findings: str
    risk: str
    actions: str
    technician: str


class ISOBuildRequest(BaseModel):
    profile: str = "workshop"
    base_distribution: str = "debian-trixie"
    include_tools: list[str] = ["smartmontools", "nvme-cli", "dmidecode", "lshw"]
    controller_url: str = "http://127.0.0.1:8000"
    auto_connect: bool = True


class GitHubSSHKeyRequest(BaseModel):
    title: str
    public_key: str


class NdeskTicketCreateRequest(BaseModel):
    title: str
    description: str
    priority: str = "normal"
    asset_external_id: str | None = None
    requester_email: str | None = None


class NdeskUserRequest(BaseModel):
    external_id: str | None = None
    email: str
    display_name: str
    role: str = "user"
    active: bool = True


class NdeskUserUpdateRequest(BaseModel):
    display_name: str | None = None
    role: str | None = None
    active: bool | None = None


class NdeskTicketEventRequest(BaseModel):
    ticket_id: str
    status: str
    run_id: int | None = None
    external_updated_at: str | None = None
    actor: str = "ndesk-webhook"
    note: str = ""


class LiveStatusEventRequest(BaseModel):
    asset_id: str
    source: str
    stage: str
    status: str
    progress_percent: int = 0
    details: str = ""


class StorageDetectRequest(BaseModel):
    asset_id: str


class StorageWipeRequest(BaseModel):
    asset_id: str
    serial_number: str
    method: str = "nvme-format"
    standard: str = "nist-800-88"


class MissionRunRequest(BaseModel):
    tenant_id: str = "default"
    asset_id: str
    serial_number: str
    device_type: str
    technician: str
    finding: str
    with_wipe: bool = True
    wipe_method: str = "nvme-format"
    wipe_standard: str = "nist-800-88"


class AgentEnrollRequest(BaseModel):
    agent_id: str
    asset_id: str
    token: str
    platform: str = "windows"
    mode: Literal["agent", "bootstick"] = "agent"


class AgentHeartbeatRequest(BaseModel):
    status: Literal["online", "degraded", "offline"] = "online"
    lease_seconds: int = 120
    details: str = ""


class OperationModuleRunRequest(BaseModel):
    module: Literal["migration", "wipe", "hardware", "seo", "pentest", "backup", "mobile"]
    asset_id: str
    tenant_id: str = "default"
    operator: str
    parameters: dict = {}


class OperationControlRequest(BaseModel):
    action: Literal["pause", "resume", "cancel", "approve", "reject"]
    actor: str
    note: str = ""


class OperationTicketLinkRequest(BaseModel):
    ticket_id: str
    relation: str = "primary"
    actor: str


class OfflineBundleRequest(BaseModel):
    run_id: int
    created_by: str
    profile: str = "bootstick-offline"
    include_tasks: list[str] = ["hardware", "wipe", "mobile"]
