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


def test_flow_wipe_execution_job_four_eyes():
    with TestClient(app) as c:
        asset = aid('e2e4')
        c.post('/api/v1/clients/register', json={"tenant_id":"default","asset_id":asset,"serial_number":"s4","device_type":"workstation"}, headers=token())
        create = c.post(
            '/api/v1/wipe/execution-jobs',
            json={"asset_id": asset, "serial_number": "disk-001", "storage_type": "nvme", "execution_mode": "boot", "created_by": "alice"},
            headers=token("operator"),
        )
        assert create.status_code == 200
        job_id = create.json()["execution_job_id"]
        bad_approve = c.post(f'/api/v1/wipe/execution-jobs/{job_id}/approve', json={"approved_by": "alice"}, headers=token("admin"))
        assert bad_approve.status_code == 400
        approve = c.post(f'/api/v1/wipe/execution-jobs/{job_id}/approve', json={"approved_by": "bob", "approval_note": "ok"}, headers=token("admin"))
        assert approve.status_code == 200
        dispatch = c.post(f'/api/v1/wipe/execution-jobs/{job_id}/dispatch', headers=token("operator"))
        assert dispatch.status_code == 200
        build = c.post(
            f'/api/v1/wipe/execution-jobs/{job_id}/agent/build',
            json={"execution_job_id": job_id, "os_target": "linux", "output_format": "tar.gz"},
            headers=token("operator"),
        )
        assert build.status_code == 200
        q = c.get(f"/api/v1/jobs/{build.json()['queue_job_id']}", headers=token("viewer"))
        assert q.status_code == 200


def test_flow_wipe_execution_job_validation_and_state_guards():
    with TestClient(app) as c:
        asset = aid('e2e5')
        c.post('/api/v1/clients/register', json={"tenant_id":"default","asset_id":asset,"serial_number":"s5","device_type":"workstation"}, headers=token())
        create = c.post(
            '/api/v1/wipe/execution-jobs',
            json={"asset_id": asset, "serial_number": "disk-001", "storage_type": "nvme", "execution_mode": "agent", "created_by": "alice"},
            headers=token("operator"),
        )
        assert create.status_code == 200
        job_id = create.json()["execution_job_id"]
        early_build = c.post(
            f'/api/v1/wipe/execution-jobs/{job_id}/agent/build',
            json={"execution_job_id": job_id, "os_target": "linux", "output_format": "zip"},
            headers=token("operator"),
        )
        assert early_build.status_code == 400
        approve = c.post(f'/api/v1/wipe/execution-jobs/{job_id}/approve', json={"approved_by": "bob", "approval_note": "ok"}, headers=token("admin"))
        assert approve.status_code == 200
        second_approve = c.post(f'/api/v1/wipe/execution-jobs/{job_id}/approve', json={"approved_by": "carol"}, headers=token("admin"))
        assert second_approve.status_code == 400
        mismatch = c.post(
            f'/api/v1/wipe/execution-jobs/{job_id}/agent/build',
            json={"execution_job_id": job_id + 1, "os_target": "linux", "output_format": "tar.gz"},
            headers=token("operator"),
        )
        assert mismatch.status_code == 400


def test_flow_wipe_execution_job_reject_and_cancel():
    with TestClient(app) as c:
        asset = aid('e2e6')
        c.post('/api/v1/clients/register', json={"tenant_id":"default","asset_id":asset,"serial_number":"s6","device_type":"workstation"}, headers=token())
        create = c.post(
            '/api/v1/wipe/execution-jobs',
            json={"asset_id": asset, "serial_number": "disk-xyz", "storage_type": "ssd", "execution_mode": "agent", "created_by": "alice"},
            headers=token("operator"),
        )
        job_id = create.json()["execution_job_id"]
        reject = c.post(
            f'/api/v1/wipe/execution-jobs/{job_id}/reject',
            json={"rejected_by": "sec-admin", "rejection_note": "missing ticket"},
            headers=token("admin"),
        )
        assert reject.status_code == 200
        dispatch_after_reject = c.post(f'/api/v1/wipe/execution-jobs/{job_id}/dispatch', headers=token("operator"))
        assert dispatch_after_reject.status_code == 400

        create2 = c.post(
            '/api/v1/wipe/execution-jobs',
            json={"asset_id": asset, "serial_number": "disk-abc", "storage_type": "hdd", "execution_mode": "boot", "created_by": "bob"},
            headers=token("operator"),
        )
        job2 = create2.json()["execution_job_id"]
        cancel = c.post(
            f'/api/v1/wipe/execution-jobs/{job2}/cancel',
            json={"canceled_by": "ops1", "cancel_note": "asset offline"},
            headers=token("operator"),
        )
        assert cancel.status_code == 200
