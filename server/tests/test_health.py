def test_health_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert data["version"] == "1.0.0"
    assert "server_time" in data
    assert "X-Request-Id" in res.headers
