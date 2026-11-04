from fastapi.testclient import TestClient

from app import main


def _build_app_without_db_init(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    return main.create_app()


def test_app_starts_without_error(monkeypatch):
    app = _build_app_without_db_init(monkeypatch)
    with TestClient(app) as _client:
        pass


def test_all_routes_registered(monkeypatch):
    app = _build_app_without_db_init(monkeypatch)
    paths = set(route.path for route in app.routes)
    expected = {
        "/api/auth/login",
        "/api/aimath/health",
        "/api/papers",
        "/api/upload",
        "/api/agent/conversations",
        "/api/export/pdfs",
        "/api/settings/classification-guidance",
    }
    for item in expected:
        assert item in paths


def test_cors_headers_present(monkeypatch):
    app = _build_app_without_db_init(monkeypatch)
    client = TestClient(app)
    resp = client.options(
        "/api/papers",
        headers={
            "Origin": "https://billfan.cn",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in (200, 204)
    assert "access-control-allow-origin" in resp.headers


def test_unauthenticated_api_returns_401(monkeypatch):
    app = _build_app_without_db_init(monkeypatch)
    client = TestClient(app)
    resp = client.get("/api/papers")
    assert resp.status_code == 401
