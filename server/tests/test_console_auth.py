"""Console auth and follow-up endpoints (TC-52, TC-53 subset)."""

from tests.conftest import console_login

MUTATE = {"X-Requested-With": "shiftmate-console"}


def test_login_logout_and_session_revocation(client):
    console_login(client, "sup.priya", "Priya-Demo-2026")
    assert client.get("/api/v1/console/me").json()["role"] == "supervisor"
    bad = client.post("/api/v1/console/auth/login", json={"username": "sup.priya", "password": "nope"})
    assert bad.status_code == 401 and bad.json()["error"]["code"] == "invalid_credentials"

    cookie = client.cookies.get("sm_session")
    assert client.post("/api/v1/console/auth/logout", headers=MUTATE).status_code == 204
    client.cookies.set("sm_session", cookie)          # replaying the old cookie must fail: logout revokes (§9.1)
    assert client.get("/api/v1/console/me").status_code == 401


def test_login_rate_limit(client):
    for _ in range(5):
        client.post("/api/v1/console/auth/login", json={"username": "trn.arjun", "password": "wrong"})
    res = client.post("/api/v1/console/auth/login", json={"username": "trn.arjun", "password": "wrong"})
    assert res.status_code == 429 and "Retry-After" in res.headers


def test_follow_up_resolve_requires_header_and_role(client, db):
    from shiftmate.models import FollowUp
    from shiftmate.time_util import utc_now

    fu = FollowUp(site_id="SITE-CHN-01", category="machine_check", group_key="machine_check:EX-07:test",
                  title="Belt switch flapping on EX-07", summary="test", priority=2, metrics={},
                  first_seen_at=utc_now(), last_seen_at=utc_now())
    db.add(fu)
    db.commit()

    console_login(client, "mec.dinesh", "Dinesh-Demo-2026")
    listed = client.get("/api/v1/console/follow-ups").json()["items"]
    assert {i["category"] for i in listed} == {"machine_check"}       # mechanic sees machine checks only
    assert client.post(f"/api/v1/console/follow-ups/{fu.follow_up_id}/resolve", json={"note": "switch replaced"}
                       ).status_code == 403                             # missing X-Requested-With
    res = client.post(f"/api/v1/console/follow-ups/{fu.follow_up_id}/resolve", json={"note": "switch replaced"},
                      headers=MUTATE)
    assert res.status_code == 200 and res.json()["status"] == "resolved"

    console_login(client, "trn.arjun", "Arjun-Demo-2026")
    assert client.get(f"/api/v1/console/follow-ups/{fu.follow_up_id}").status_code == 404   # not a trainer category
