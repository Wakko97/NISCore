from fastapi.testclient import TestClient

from app.main import app
from app.security import issue_token


def test_me_requires_auth():
    with TestClient(app) as c:
        r = c.get('/api/v1/auth/me')
    assert r.status_code == 401


def test_viewer_cannot_write_clients():
    token = issue_token('viewer-user', 'viewer', ttl_minutes=10)
    with TestClient(app) as c:
        r = c.post('/api/v1/clients/register', json={"tenant_id":"default","asset_id":"deny-1","serial_number":"s","device_type":"laptop"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
