"""Open-Meteo forecast feed (T46 / S8, §6.5): mapping, upsert, `forecast.upsert` to devices, failure keeps old rows.
Open-Meteo is mocked with httpx.MockTransport; no network."""

import httpx

from shiftmate.models import ChangeLog, Forecast
from shiftmate.services.forecast import refresh_all, visibility_band, weather_for
from tests.conftest import make_device_auth_headers, pair

HOURS = ["2031-01-01T00:00", "2031-01-01T01:00", "2031-01-01T02:00", "2031-01-01T03:00", "2031-01-01T04:00"]


def _payload():
    return {
        "hourly": {
            "time": HOURS,
            "temperature_2m": [31.0, 29.0, 27.5, 26.0, 25.0],
            "apparent_temperature": [36.0, 33.0, 30.0, 28.0, None],
            "precipitation": [1.2, 0.0, 0.0, 0.0, None],  # last hour incomplete → skipped
            "wind_speed_10m": [10.0, 45.0, 5.0, 5.0, 5.0],
            "visibility": [8000.0, 12000.0, 600.0, 3000.0, 20000.0],
            "relative_humidity_2m": [80, 70, 95, 90, 85],
        }
    }


def _client(requests: list, status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status, json=_payload() if status == 200 else {"error": True})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_mapping_rules():
    assert weather_for(0.5, 50, 500) == "rain"
    assert weather_for(0.0, 38, 500) == "windy"
    assert weather_for(0.0, 10, 999) == "foggy"
    assert weather_for(0.0, 10, None) == "clear"
    assert [visibility_band(v) for v in (None, 5000, 4999, 999)] == ["good", "good", "moderate", "poor"]


def test_fetch_upserts_rows_and_reaches_the_device(client, db):
    requests: list[httpx.Request] = []
    assert refresh_all(_client(requests), site_id="SITE-CHN-01") == {"SITE-CHN-01": "ok (4 hours)"}
    url = requests[0].url
    assert url.host == "api.open-meteo.com" and url.params["timezone"] == "UTC"
    assert url.params["forecast_days"] == "2" and "visibility" in url.params["hourly"]

    rows = (
        db.query(Forecast)
        .filter(Forecast.site_id == "SITE-CHN-01", Forecast.source == "open_meteo")
        .order_by(Forecast.valid_from)
        .all()
    )
    assert [r.weather for r in rows] == ["rain", "windy", "foggy", "clear"]
    assert [r.visibility for r in rows] == ["good", "good", "poor", "moderate"]
    assert rows[0].heat_index_c == 36.0 and rows[0].issued_at is not None

    device_id, secret = pair(client)
    path = "/api/v1/sync/pull?cursor=0&limit=500"
    changes = client.get(path, headers=make_device_auth_headers("GET", path, b"", device_id, secret)).json()[
        "changes"
    ]
    upserts = [c for c in changes if c["change_type"] == "forecast.upsert"]
    assert upserts and upserts[-1]["scope_id"] == "SITE-CHN-01"
    hour = upserts[-1]["payload"]["hours"][0]
    assert hour["source"] == "open_meteo" and hour["issued_at"].endswith("Z")  # age is shown from issued_at


def test_failure_keeps_the_last_forecast(db):
    before = db.query(Forecast).filter(Forecast.site_id == "SITE-BLR-02").count()
    changes = db.query(ChangeLog).count()
    result = refresh_all(_client([], status=503), site_id="SITE-BLR-02")
    assert result["SITE-BLR-02"].startswith("error")
    db.expire_all()
    assert db.query(Forecast).filter(Forecast.site_id == "SITE-BLR-02").count() == before
    assert db.query(ChangeLog).count() == changes
