from pydantic import BaseModel


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
