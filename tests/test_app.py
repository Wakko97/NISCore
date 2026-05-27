from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app


init_db()


def test_health_endpoint_contains_metadata():
    with TestClient(app) as client:
        r = client.get('/health')
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'ok'
    assert 'version' in data
    assert 'env' in data


def test_ready_endpoint_works():
    with TestClient(app) as client:
        r = client.get('/ready')
    assert r.status_code == 200
    assert r.json()['status'] == 'ready'


def test_root_contains_version():
    with TestClient(app) as client:
        r = client.get('/')
    assert r.status_code == 200
    assert app.version in r.text
