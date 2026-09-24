"""Open-Meteo forecast feed (technical spec T46 / S8, §6.5, V-12).

Fetches 48 hourly values per site and upserts `forecasts` rows (source `open_meteo`, `issued_at` = fetch time), then
records a `forecast.upsert` change for the site. Weather: rain if precipitation ≥ 0.5 mm, windy if wind ≥ 38 km/h,
foggy if visibility < 1 000 m, else clear (dust never comes from Open-Meteo). The response is untrusted: validated and
clamped. Any failure keeps the last stored forecast (the device shows its age); the seeded forecast stays if a site was
never fetched.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from shiftmate.config import settings
from shiftmate.db import SessionLocal
from shiftmate.models import Forecast, Site
from shiftmate.services.changes import record_change
from shiftmate.time_util import iso_ms, utc_now

log = logging.getLogger("shiftmate.forecast")

URL = "https://api.open-meteo.com/v1/forecast"
HOURLY = "temperature_2m,apparent_temperature,precipitation,wind_speed_10m,visibility,relative_humidity_2m"
TIMEOUT_S = 5.0


class _Hourly(BaseModel):
    time: list[str]
    temperature_2m: list[float | None]
    apparent_temperature: list[float | None]
    precipitation: list[float | None]
    wind_speed_10m: list[float | None]
    visibility: list[float | None]


class _Response(BaseModel):
    hourly: _Hourly


def _clamp(value: float | None, lo: float, hi: float) -> float | None:
    return None if value is None else min(max(float(value), lo), hi)


def weather_for(precipitation_mm: float, wind_kmh: float, visibility_m: float | None) -> str:
    if precipitation_mm >= 0.5:
        return "rain"
    if wind_kmh >= 38:
        return "windy"
    if visibility_m is not None and visibility_m < 1000:
        return "foggy"
    return "clear"


def visibility_band(visibility_m: float | None) -> str:
    """§8.6.2 bands (darkness is applied on the device at estimate time)."""
    if visibility_m is None or visibility_m >= 5000:
        return "good"
    return "moderate" if visibility_m >= 1000 else "poor"


def forecast_hour(f: Forecast) -> dict[str, Any]:
    """`ForecastHour` wire shape (§6.2 bootstrap and `forecast.upsert`)."""
    return {
        "valid_from": iso_ms(f.valid_from),
        "valid_to": iso_ms(f.valid_to),
        "weather": f.weather,
        "visibility": f.visibility,
        "visibility_m": f.visibility_m,
        "temp_c": f.temp_c,
        "heat_index_c": f.heat_index_c,
        "wind_kmh": f.wind_kmh,
        "precipitation_mm": f.precipitation_mm,
        "issued_at": iso_ms(f.issued_at),
        "source": f.source,
    }


def fetch_site(db: Session, site: Site, client: httpx.Client) -> list[Forecast]:
    """Fetches and upserts one site's forecast. Raises on HTTP/validation errors; the caller keeps old rows."""
    params = {
        "latitude": site.lat,
        "longitude": site.lon,
        "hourly": HOURLY,
        "timezone": "UTC",
        "forecast_days": 2,
    }
    res = client.get(URL, params=params, timeout=TIMEOUT_S)
    res.raise_for_status()
    hourly = _Response.model_validate(res.json()).hourly
    issued = utc_now()
    rows: list[Forecast] = []
    for i, t in enumerate(hourly.time):
        temp = _clamp(hourly.temperature_2m[i], -60, 70)
        wind = _clamp(hourly.wind_speed_10m[i], 0, 300)
        rain = _clamp(hourly.precipitation[i], 0, 500)
        if temp is None or wind is None or rain is None:
            continue  # incomplete hour: keep whatever is stored for it
        vis = _clamp(hourly.visibility[i], 0, 100_000)
        valid_from = datetime.fromisoformat(t).replace(tzinfo=None)  # Open-Meteo UTC "YYYY-MM-DDTHH:MM"
        row = Forecast(
            site_id=site.site_id,
            valid_from=valid_from,
            valid_to=valid_from + timedelta(hours=1),
            weather=weather_for(rain, wind, vis),
            visibility=visibility_band(vis),
            visibility_m=vis,
            temp_c=temp,
            heat_index_c=_clamp(hourly.apparent_temperature[i], -60, 80),
            wind_kmh=wind,
            precipitation_mm=rain,
            issued_at=issued,
            source="open_meteo",
        )
        rows.append(db.merge(row))
    if not rows:
        raise ValueError("no complete forecast hours in the response")
    db.flush()
    record_change(
        db,
        "forecast.upsert",
        "site",
        site.site_id,
        {"site_id": site.site_id, "hours": [forecast_hour(r) for r in rows]},
    )
    return rows


def refresh_all(client: httpx.Client | None = None, site_id: str | None = None) -> dict[str, str]:
    """Refreshes every site (or one). Returns `{site_id: "ok (n hours)" | "error: …"}`; never raises."""
    own_client = client is None
    client = client or httpx.Client()
    results: dict[str, str] = {}
    db = SessionLocal()
    try:
        q = db.query(Site)
        if site_id:
            q = q.filter(Site.site_id == site_id)
        for site in q.order_by(Site.site_id).all():
            try:
                rows = fetch_site(db, site, client)
                db.commit()
                results[site.site_id] = f"ok ({len(rows)} hours)"
            except (httpx.HTTPError, ValidationError, ValueError, KeyError, IndexError) as exc:
                db.rollback()
                log.warning("forecast_fetch_failed site=%s error=%s", site.site_id, exc)
                results[site.site_id] = f"error: {exc}"
    finally:
        db.close()
        if own_client:
            client.close()
    return results


async def poll_forever() -> None:
    """Background poller (FORECAST_ENABLED): refresh now, then every FORECAST_POLL_MINUTES."""
    while True:
        await asyncio.to_thread(refresh_all)
        await asyncio.sleep(max(1, settings.FORECAST_POLL_MINUTES) * 60)
