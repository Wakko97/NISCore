from uuid import uuid4
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app
from app.security import issue_token


init_db()


def token(role="admin"):
    return {"Authorization": f"Bearer {issue_token('e2e', role, ttl_minutes=120)}"}


def aid(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def test_flow_client_register_and_list():
    with TestClient(app) as c:
        r = c.post('/api/v1/clients/register', json={"tenant_id":"default","asset_id":aid('e2e1'),"serial_number":"s1","device_type":"laptop"}, headers=token())
        assert r.status_code == 200
        lst = c.get('/api/v1/clients?limit=5')
        assert lst.status_code == 200


def test_flow_diagnostic_upload():
    with TestClient(app) as c:
        asset = aid('e2e2')
        c.post('/api/v1/clients/register', json={"tenant_id":"default","asset_id":asset,"serial_number":"s2","device_type":"laptop"}, headers=token())
        r = c.post('/api/v1/diagnostics/results', json={"asset_id":asset,"technician":"alice","result":"ok","raw_json":"{}"}, headers=token())
        assert r.status_code == 200


def test_flow_wipe_and_certificate():
    with TestClient(app) as c:
        asset = aid('e2e3')
        c.post('/api/v1/clients/register', json={"tenant_id":"default","asset_id":asset,"serial_number":"s3","device_type":"laptop"}, headers=token())
        w = c.post('/api/v1/wipe/jobs', json={"asset_id":asset,"method":"quick","standard":"nist"}, headers=token())
        assert w.status_code == 200
        cert_id = w.json()["certificate_id"]
        g = c.get(f'/api/v1/wipe/certificates/{cert_id}')
        assert g.status_code == 200


def test_flow_migration_job_queue():
    with TestClient(app) as c:
        r = c.post('/api/v1/migrations/jobs', json={"tenant_id":"default","job_type":"imap","source":"a","target":"b"}, headers=token())
        assert r.status_code == 200
        j = c.get(f"/api/v1/jobs/{r.json()['queue_job_id']}", headers=token("viewer"))
        assert j.status_code == 200


def test_flow_iso_queue():
    with TestClient(app) as c:
        r = c.post('/api/v1/workshop/iso/build', json={"profile":"workshop","base_distribution":"debian","include_tools":["nvme-cli"]}, headers=token())
        assert r.status_code == 200


def test_flow_mission_run():
    with TestClient(app) as c:
        payload = {
            "tenant_id": "default",
            "asset_id": aid("mission"),
            "serial_number": "m1",
            "device_type": "laptop",
            "technician": "alice",
            "finding": "smart_critical",
            "with_wipe": True,
        }
        r = c.post('/api/v1/missions/run', json=payload, headers=token())
        assert r.status_code == 200
        data = r.json()
        assert data["recommendation"]["priority"] == "P1"
        assert data["wipe"]["certificate_id"] > 0
