from __future__ import annotations

import hashlib
import socket
import os
import ssl
from datetime import datetime, timezone

import httpx


def hash_chain(prev_hash: str, body: str, created_at: datetime) -> str:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    value = f"{prev_hash}|{body}|{created_at.astimezone(timezone.utc).isoformat()}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sign_like(data: str) -> tuple[str, str]:
    sha = hashlib.sha256(data.encode("utf-8")).hexdigest()
    return sha, f"sig:{sha[:16]}"


def recommend_for_finding(finding_type: str, detail: str) -> dict:
    mapping = {
        "smart_critical": ("P1", "Backup sofort starten; Datenträger tauschen; Ticket P1 eröffnen", "hoch"),
        "ssl_expiry": ("P1", "Zertifikat erneuern; Deployment prüfen; Monitoring scharf schalten", "hoch"),
        "ransomware_indicator": ("P1", "Host isolieren; IOC-Sweep starten; Restore-Fähigkeit prüfen", "kritisch"),
        "malware_indicator": ("P1", "EDR-Scan ausführen; Quarantäne prüfen; IOC-Abgleich", "hoch"),
        "backup_missing": ("P1", "Ad-hoc Backup auslösen; Restore-Test einplanen", "hoch"),
        "server_health_warn": ("P2", "Wartungsfenster planen; Services prüfen; Kapazität skalieren", "mittel"),
    }
    if finding_type in mapping:
        p, a, r = mapping[finding_type]
        return {"priority": p, "action": a, "risk": r}
    return {"priority": "P3", "action": f"Analyse vertiefen: {detail}", "risk": "mittel"}


def ssl_days_until_expiry(host: str, port: int = 443) -> int:
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
    expires = cert["notAfter"]
    dt = datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    return (dt - datetime.now(timezone.utc)).days


class NdeskClientError(RuntimeError):
    pass


def _ndesk_settings() -> tuple[str, str]:
    base_url = os.getenv("NDESK_BASE_URL", "").strip().rstrip("/")
    token = os.getenv("NDESK_API_TOKEN", "").strip()
    if not base_url or not token:
        raise NdeskClientError("NDESK_BASE_URL und NDESK_API_TOKEN müssen gesetzt sein")
    return base_url, token


def ndesk_request(method: str, path: str, payload: dict | None = None, params: dict | None = None) -> dict:
    base_url, token = _ndesk_settings()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"

    with httpx.Client(timeout=15) as client:
        response = client.request(method, f"{base_url}{path}", json=payload, params=params, headers=headers)

    if response.status_code >= 400:
        raise NdeskClientError(f"NDesk Fehler {response.status_code}: {response.text[:300]}")

    if not response.text:
        return {"ok": True}
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}
