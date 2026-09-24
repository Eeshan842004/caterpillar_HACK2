import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from shiftmate.config import settings
from shiftmate.db import Base, SessionLocal, engine
from shiftmate.models import (
    ConsoleUser,
    FleetStatus,
    Forecast,
    Handover,
    HandoverItem,
    Incident,
    Machine,
    MachineProfile,
    Operator,
    PairingCode,
    Site,
    TaskAssignment,
    Zone,
)


def seed_database(db: Session | None = None) -> dict:
    close_after = False
    if db is None:
        db = SessionLocal()
        close_after = True

    try:
        content_path = settings.content_path
        seed_file = content_path / "seed" / "demo_seed.json"
        if not seed_file.exists():
            raise FileNotFoundError(f"Seed file not found at {seed_file}")

        with open(seed_file, "r", encoding="utf-8") as f:
            seed_data = json.load(f)

        # 1. Machine Profiles
        profiles_dir = content_path / "profiles"
        if profiles_dir.exists():
            for p_file in profiles_dir.glob("*.json"):
                with open(p_file, "r", encoding="utf-8") as pf:
                    p_data = json.load(pf)
                profile = MachineProfile(
                    profile_id=p_data["profile_id"],
                    version=p_data["version"],
                    machine_class=p_data["machine_class"],
                    body=p_data,
                    published_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                db.merge(profile)

        # 2. Sites
        for s in seed_data.get("sites", []):
            site = Site(
                site_id=s["site_id"],
                name=s["name"],
                sector=s["sector"],
                lat=s["lat"],
                lon=s["lon"],
                utc_offset_minutes=s.get("utc_offset_minutes", 330),
                diesel_price_inr_per_l=s.get("diesel_price_inr_per_l", 92.00),
                dark_start_local=s.get("dark_start_local", "19:00"),
                dark_end_local=s.get("dark_end_local", "06:00"),
                job_efficiency_override=s.get("job_efficiency_override"),
                congestion_level=s.get("congestion_level", "medium"),
                data_origin=s.get("data_origin", "demo_seed"),
            )
            db.merge(site)

        # 3. Zones
        for z in seed_data.get("zones", []):
            zone = Zone(
                zone_id=z["zone_id"],
                site_id=z["site_id"],
                name=z["name"],
                kind=z["kind"],
                center_lat=z["center_lat"],
                center_lon=z["center_lon"],
                radius_m=z["radius_m"],
                speed_limit_kmh=z.get("speed_limit_kmh"),
            )
            db.merge(zone)

        # 4. Machines
        for m in seed_data.get("machines", []):
            machine = Machine(
                machine_id=m["machine_id"],
                short_id=m["short_id"],
                site_id=m["site_id"],
                profile_id=m["profile_id"],
                profile_version=m["profile_version"],
                model_name=m["model_name"],
                year_of_manufacture=m["year_of_manufacture"],
                detail_level=m["detail_level"],
                data_origin=m.get("data_origin", "demo_seed"),
            )
            db.merge(machine)

        # 5. Operators
        for o in seed_data.get("operators", []):
            op = Operator(
                operator_id=o["operator_id"],
                display_name=o["display_name"],
                language=o["language"],
                skill_level=o["skill_level"],
                experience_months=o["experience_months"],
                hired_at=datetime.strptime(o["hired_at"], "%Y-%m-%d").date(),
                site_id=o["site_id"],
                pin_salt=o["pin_salt"],
                pin_hash=o["pin_hash"],
                pin_iterations=o.get("pin_iterations", 20000),
                data_origin=o.get("data_origin", "demo_seed"),
            )
            db.merge(op)

        # 6. Console Users
        for u in seed_data.get("console_users", []):
            user = db.query(ConsoleUser).filter(ConsoleUser.username == u["username"]).first()
            if not user:
                user = ConsoleUser(
                    username=u["username"],
                    display_name=u["display_name"],
                    role=u["role"],
                    site_ids=u["site_ids"],
                    password_hash=u["password_hash"],
                )
                db.add(user)
            else:
                user.display_name = u["display_name"]
                user.role = u["role"]
                user.site_ids = u["site_ids"]
                user.password_hash = u["password_hash"]

        # 7. Pairing Codes
        for pc in seed_data.get("pairing_codes", []):
            expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=pc.get("expires_in_days", 365))
            code_obj = PairingCode(
                code=pc["code"],
                machine_id=pc["machine_id"],
                reusable=pc.get("reusable", True),
                expires_at=expires,
            )
            db.merge(code_obj)

        # 8. Task Assignments — day offsets map to the SITE-LOCAL date, and "HH:MM" planned starts are site-local
        #    times converted to UTC (audit: they were stored as if they were UTC, 5.5 h off)
        sites_by_id = {s["site_id"]: s for s in seed_data.get("sites", [])}
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        for a in seed_data.get("assignments", []):
            offset = timedelta(minutes=sites_by_id[a["site_id"]].get("utc_offset_minutes", 330))
            site_today = (now_utc + offset).date()
            p_date = site_today + timedelta(days=a.get("planned_day_offset", 0))
            p_start = None
            if a.get("planned_start_local"):
                hh, mm = a["planned_start_local"].split(":")
                p_start = datetime.combine(p_date, datetime.min.time()) + timedelta(hours=int(hh), minutes=int(mm)) - offset

            task = TaskAssignment(
                task_id=a["task_id"],
                site_id=a["site_id"],
                machine_id=a.get("machine_id"),
                task_type=a["task_type"],
                zone_id=a.get("zone_id"),
                location_text=a["location_text"],
                quantity=a["quantity"],
                unit=a["unit"],
                material=a["material"],
                priority=a.get("priority", 2),
                completion_criterion=a["completion_criterion"],
                planner_minutes=a.get("planner_minutes"),
                planned_date=p_date,
                planned_start_at=p_start,
                planned_start_window_min=a.get("planned_start_window_min", 15),
                sequence=a["sequence"],
                source=a.get("source", "seed"),
                revision=1,
                status="assigned",
                exec_state="PLANNED",
                data_origin="demo_seed",
            )
            db.merge(task)

        # 9. Forecasts — hour offsets are relative to the current SITE-LOCAL hour; issued 18:00 local yesterday
        for fc in seed_data.get("forecast", []):
            offset = timedelta(minutes=sites_by_id[fc["site_id"]].get("utc_offset_minutes", 330))
            local_hour = (now_utc + offset).replace(minute=0, second=0, microsecond=0)
            base_hour = local_hour - offset
            v_from = base_hour + timedelta(hours=fc["hour_offset"])
            v_to = v_from + timedelta(hours=1)
            forecast = Forecast(
                site_id=fc["site_id"],
                valid_from=v_from,
                valid_to=v_to,
                weather=fc["weather"],
                visibility=fc["visibility"],
                visibility_m=fc.get("visibility_m"),
                temp_c=fc["temp_c"],
                heat_index_c=fc.get("heat_index_c"),
                wind_kmh=fc["wind_kmh"],
                precipitation_mm=fc["precipitation_mm"],
                issued_at=datetime.combine((now_utc + offset).date() - timedelta(days=1), datetime.min.time())
                + timedelta(hours=18) - offset,
                source=fc.get("source", "seed"),
            )
            db.merge(forecast)

        db.flush()                               # the session does not autoflush; lookups below need rows 1-9

        # 10. Seeded machine-fault incident referenced by the EX-07 handover (tech §5.4.2)
        for ho in seed_data.get("handovers", []):
            for item in ho["items"]:
                if item.get("incident_id") and db.get(Incident, item["incident_id"]) is None:
                    machine = db.get(Machine, ho["machine_id"])
                    occurred = now_utc + timedelta(minutes=ho.get("created_offset_min", -480) - 60)
                    db.add(Incident(
                        incident_id=item["incident_id"], machine_id=ho["machine_id"], operator_id=ho.get("from_operator_id"),
                        site_id=machine.site_id, occurred_at=occurred, type="machine_fault", severity="medium",
                        status="reported", origin="operator",
                        fields={"type": {"value": "machine_fault", "source": "reported", "entry_id": None},
                                "severity": {"value": "medium", "source": "reported", "entry_id": None}},
                        created_at=occurred, updated_at=occurred,
                    ))
            # 11. Previous-shift handover (open items the incoming operator must acknowledge)
            if db.get(Handover, ho["handover_id"]) is None:
                db.add(Handover(handover_id=ho["handover_id"], machine_id=ho["machine_id"],
                                from_operator_id=ho.get("from_operator_id"), wording_method="template",
                                created_at=now_utc + timedelta(minutes=ho.get("created_offset_min", -480)),
                                data_origin="demo_seed"))
                db.flush()
                for item in ho["items"]:
                    db.add(HandoverItem(item_id=item["item_id"], handover_id=ho["handover_id"],
                                        item_type=item["item_type"], text=item["text"], audiences=item["audiences"],
                                        source_entry_ids=[], task_id=item.get("task_id"),
                                        incident_id=item.get("incident_id"), status=item.get("status", "open")))

        # 12. Fleet status for all machines (S6 view), status only
        for m in seed_data.get("machines", []):
            if db.get(FleetStatus, m["machine_id"]) is None:
                db.add(FleetStatus(machine_id=m["machine_id"], state="OFF", open_alerts=0, last_sync_at=None,
                                   data_origin="demo_seed"))

        db.commit()

        counts = {
            "sites": db.query(Site).count(),
            "zones": db.query(Zone).count(),
            "machines": db.query(Machine).count(),
            "operators": db.query(Operator).count(),
            "console_users": db.query(ConsoleUser).count(),
            "pairing_codes": db.query(PairingCode).count(),
            "tasks": db.query(TaskAssignment).count(),
        }
        return counts

    finally:
        if close_after:
            db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    results = seed_database()
    print("Seed completed successfully:", results)
