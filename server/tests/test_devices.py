from tests.conftest import make_device_auth_headers


def test_device_pairing_and_bootstrap(client):
    # 1. Pair device to EX-07
    pair_payload = {
        "pairing_code": "100007",
        "machine_id": "EX-07",
        "device_label": "Cab Tablet EX-07",
    }
    res = client.post("/api/v1/devices/pair", json=pair_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["machine_id"] == "EX-07"
    assert data["site_id"] == "SITE-CHN-01"
    assert data["profile_id"] == "excavator_20t"
    device_id = data["device_id"]
    device_secret = data["device_secret"]

    # 2. Test Invalid pairing code
    res_bad = client.post(
        "/api/v1/devices/pair",
        json={"pairing_code": "999999", "machine_id": "EX-07", "device_label": "Bad"},
    )
    assert res_bad.status_code == 404
    assert res_bad.json()["error"]["code"] == "pairing_code_invalid"

    # 3. Test Bootstrap
    path = "/api/v1/devices/bootstrap"
    headers = make_device_auth_headers("GET", path, b"", device_id, device_secret)
    res_boot = client.get(path, headers=headers)
    assert res_boot.status_code == 200
    boot_data = res_boot.json()
    assert boot_data["site"]["site_id"] == "SITE-CHN-01"
    assert len(boot_data["zones"]) > 0
    assert len(boot_data["machines"]) > 0
    assert len(boot_data["operators"]) > 0
    assert "assignments" in boot_data

    # 4. Test Rebind to HT-03
    rebind_payload = {
        "machine_id": "HT-03",
        "pairing_code": "300003",
    }
    rebind_path = "/api/v1/devices/rebind"
    import json

    rebind_bytes = json.dumps(rebind_payload).encode()
    rebind_headers = make_device_auth_headers("POST", rebind_path, rebind_bytes, device_id, device_secret)
    rebind_headers["Content-Type"] = "application/json"
    res_rebind = client.post(rebind_path, content=rebind_bytes, headers=rebind_headers)
    assert res_rebind.status_code == 200
    assert res_rebind.json()["machine_id"] == "HT-03"
