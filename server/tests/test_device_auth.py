import time

from tests.conftest import make_device_auth_headers


def test_device_auth_security(client):
    # Pair device to get valid ID & secret
    res = client.post(
        "/api/v1/devices/pair",
        json={"pairing_code": "100007", "machine_id": "EX-07", "device_label": "Auth Test"},
    )
    assert res.status_code == 200
    data = res.json()
    device_id = data["device_id"]
    device_secret = data["device_secret"]

    path = "/api/v1/devices/bootstrap"

    # 1. Missing headers
    res_no_headers = client.get(path)
    assert res_no_headers.status_code == 401
    assert res_no_headers.json()["error"]["code"] == "unauthenticated"

    # 2. Timestamp skew (10 minutes in the past)
    skewed_ts = int(time.time() * 1000) - 600000
    headers_skew = make_device_auth_headers("GET", path, b"", device_id, device_secret, timestamp_ms=skewed_ts)
    res_skew = client.get(path, headers=headers_skew)
    assert res_skew.status_code == 401
    assert res_skew.json()["error"]["code"] == "timestamp_skew"

    # 3. Bad signature
    headers_bad_sig = make_device_auth_headers("GET", path, b"", device_id, device_secret)
    headers_bad_sig["X-Signature"] = "0" * 64
    res_bad_sig = client.get(path, headers=headers_bad_sig)
    assert res_bad_sig.status_code == 401
    assert res_bad_sig.json()["error"]["code"] == "signature_invalid"

    # 4. Unknown device
    headers_unknown = make_device_auth_headers("GET", path, b"", "00000000-0000-0000-0000-000000000000", device_secret)
    res_unknown = client.get(path, headers=headers_unknown)
    assert res_unknown.status_code == 401
    assert res_unknown.json()["error"]["code"] == "device_unknown"
