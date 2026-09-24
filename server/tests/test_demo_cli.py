"""Demo command helpers (docs/DEMO_RUNBOOK.md): schema adoption, status banner, LAN CORS."""

from fastapi.testclient import TestClient

from shiftmate import demo
from shiftmate.config import settings


def test_migrate_adopts_a_create_all_database_then_is_idempotent(db):
    # The test database was built with create_all (no recorded revision) → adopted, then already at head
    assert demo.migrate() in ("existing database adopted (stamped at head)", "schema at head")
    assert demo.migrate() == "schema at head"


def test_banner_lists_what_the_presenter_needs(db):
    text = demo.banner(8000, demo.status(db))
    for needle in (
        "Tablet server URL",
        ":8000",
        "100007 EX-07",
        "300003 HT-03",
        "Ravi OP-0007 on EX-07 (1234)",
        "sup.priya / Priya-Demo-2026",
        "estimator.excavator@1",
        "within 5 min",
    ):
        assert needle in text


def test_lan_cors_allows_private_origins_only(monkeypatch):
    monkeypatch.setattr(settings, "CORS_ALLOW_LAN", True)
    from shiftmate.main import create_app

    client = TestClient(create_app())
    headers = {"Access-Control-Request-Method": "GET"}
    ok = client.options("/api/v1/health", headers={**headers, "Origin": "http://192.168.1.20:8081"})
    assert ok.headers.get("access-control-allow-origin") == "http://192.168.1.20:8081"
    bad = client.options("/api/v1/health", headers={**headers, "Origin": "http://example.com"})
    assert "access-control-allow-origin" not in bad.headers
