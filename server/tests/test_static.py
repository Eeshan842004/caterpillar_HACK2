"""Static hosting (DR-07, §4.4 static.py): /console SPA fallback, /app COOP/COEP headers, skipped when missing."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from shiftmate.static import mount_static


def _app(tmp_path):
    console, operator = tmp_path / "console", tmp_path / "operator"
    (console / "assets").mkdir(parents=True)
    (console / "index.html").write_text("<html>console</html>", encoding="utf-8")
    (console / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (operator / "tasks").mkdir(parents=True)
    (operator / "index.html").write_text("<html>operator</html>", encoding="utf-8")
    (operator / "tasks" / "index.html").write_text("<html>tasks</html>", encoding="utf-8")
    (operator / "sqlite.wasm").write_bytes(b"\x00asm")
    app = FastAPI()
    assert mount_static(app, str(console), str(operator)) == ["/console", "/app"]
    return TestClient(app)


def test_console_spa_fallback(tmp_path):
    client = _app(tmp_path)
    assert client.get("/console/assets/app.js").text == "console.log(1)"
    for path in ("/console/", "/console/follow-ups/abc", "/console/incidents"):
        res = client.get(path)
        assert res.status_code == 200 and res.text == "<html>console</html>", path


def test_operator_app_is_cross_origin_isolated(tmp_path):
    client = _app(tmp_path)
    for path, body in (("/app/", "<html>operator</html>"), ("/app/tasks/", "<html>tasks</html>")):
        res = client.get(path)
        assert res.status_code == 200 and res.text == body
        assert res.headers["cross-origin-opener-policy"] == "same-origin"
        assert res.headers["cross-origin-embedder-policy"] == "credentialless"
    wasm = client.get("/app/sqlite.wasm")
    assert wasm.headers["content-type"] == "application/wasm"
    assert wasm.headers["cross-origin-embedder-policy"] == "credentialless"
    missing = client.get("/app/nope.js")
    assert missing.status_code == 404 and missing.headers["cross-origin-opener-policy"] == "same-origin"


def test_missing_dirs_are_skipped(tmp_path):
    app = FastAPI()
    assert mount_static(app, str(tmp_path / "none"), None) == []
    assert TestClient(app).get("/console/").status_code == 404
