import json
import hashlib
from pathlib import Path
import argon2

def make_seed():
    ph = argon2.PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
    
    sites = [
        {
            "site_id": "SITE-CHN-01",
            "name": "Chennai Construction Site A",
            "sector": "construction",
            "lat": 12.83,
            "lon": 79.95,
            "utc_offset_minutes": 330,
            "diesel_price_inr_per_l": 92.00,
            "dark_start_local": "19:00",
            "dark_end_local": "06:00",
            "job_efficiency_override": None,
            "congestion_level": "medium",
            "data_origin": "demo_seed"
        },
        {
            "site_id": "SITE-BLR-02",
            "name": "Bengaluru Construction Site B",
            "sector": "construction",
            "lat": 13.08,
            "lon": 77.58,
            "utc_offset_minutes": 330,
            "diesel_price_inr_per_l": 90.50,
            "dark_start_local": "19:00",
            "dark_end_local": "06:00",
            "job_efficiency_override": None,
            "congestion_level": "low",
            "data_origin": "demo_seed"
        },
        {
            "site_id": "SITE-MIN-03",
            "name": "Jharkhand Open Pit C",
            "sector": "mining",
            "lat": 23.75,
            "lon": 86.42,
            "utc_offset_minutes": 330,
            "diesel_price_inr_per_l": 94.00,
            "dark_start_local": "18:30",
            "dark_end_local": "05:30",
            "job_efficiency_override": None,
            "congestion_level": "high",
            "data_origin": "demo_seed"
        },
        {
            "site_id": "SITE-MIN-04",
            "name": "Singrauli Open Pit D",
            "sector": "mining",
            "lat": 24.20,
            "lon": 82.67,
            "utc_offset_minutes": 330,
            "diesel_price_inr_per_l": 93.00,
            "dark_start_local": "18:30",
            "dark_end_local": "05:30",
            "job_efficiency_override": None,
            "congestion_level": "medium",
            "data_origin": "demo_seed"
        }
    ]

    zones = [
        {"zone_id": "Z-CHN-TR1", "site_id": "SITE-CHN-01", "name": "Trench Area T1", "kind": "trench_area", "center_lat": 12.831, "center_lon": 79.951, "radius_m": 60.0, "speed_limit_kmh": None},
        {"zone_id": "Z-CHN-TR2", "site_id": "SITE-CHN-01", "name": "Trench Area T2", "kind": "trench_area", "center_lat": 12.833, "center_lon": 79.953, "radius_m": 60.0, "speed_limit_kmh": None},
        {"zone_id": "Z-CHN-LB2", "site_id": "SITE-CHN-01", "name": "Loading Bay 2", "kind": "loading_bay", "center_lat": 12.830, "center_lon": 79.950, "radius_m": 40.0, "speed_limit_kmh": None},
        {"zone_id": "Z-CHN-YARD", "site_id": "SITE-CHN-01", "name": "Yard", "kind": "yard", "center_lat": 12.828, "center_lon": 79.948, "radius_m": 80.0, "speed_limit_kmh": 15.0},
        
        {"zone_id": "Z-BLR-TR1", "site_id": "SITE-BLR-02", "name": "Excavation Zone 1", "kind": "trench_area", "center_lat": 13.081, "center_lon": 77.581, "radius_m": 70.0, "speed_limit_kmh": None},
        {"zone_id": "Z-BLR-YARD", "site_id": "SITE-BLR-02", "name": "Main Yard", "kind": "yard", "center_lat": 13.080, "center_lon": 77.580, "radius_m": 80.0, "speed_limit_kmh": 15.0},
        
        {"zone_id": "Z-MIN-SH1", "site_id": "SITE-MIN-03", "name": "Shovel 1", "kind": "shovel", "center_lat": 23.751, "center_lon": 86.421, "radius_m": 80.0, "speed_limit_kmh": None},
        {"zone_id": "Z-MIN-CR", "site_id": "SITE-MIN-03", "name": "Crusher", "kind": "crusher", "center_lat": 23.755, "center_lon": 86.425, "radius_m": 80.0, "speed_limit_kmh": 20.0},
        {"zone_id": "Z-MIN-R3", "site_id": "SITE-MIN-03", "name": "Road 3", "kind": "haul_road", "center_lat": 23.753, "center_lon": 86.423, "radius_m": 300.0, "speed_limit_kmh": 35.0},
        {"zone_id": "Z-MIN-R1", "site_id": "SITE-MIN-03", "name": "Ramp 1", "kind": "haul_road", "center_lat": 23.752, "center_lon": 86.422, "radius_m": 200.0, "speed_limit_kmh": 25.0},
        {"zone_id": "Z-MIN-YARD", "site_id": "SITE-MIN-03", "name": "Pit Yard", "kind": "yard", "center_lat": 23.749, "center_lon": 86.419, "radius_m": 100.0, "speed_limit_kmh": 20.0},
        {"zone_id": "Z-MIN-DUMP", "site_id": "SITE-MIN-03", "name": "Overburden Dump", "kind": "dump", "center_lat": 23.758, "center_lon": 86.428, "radius_m": 120.0, "speed_limit_kmh": 25.0},
        
        {"zone_id": "Z-MIN4-SH1", "site_id": "SITE-MIN-04", "name": "North Shovel", "kind": "shovel", "center_lat": 24.201, "center_lon": 82.671, "radius_m": 80.0, "speed_limit_kmh": None},
        {"zone_id": "Z-MIN4-DUMP", "site_id": "SITE-MIN-04", "name": "South Dump", "kind": "dump", "center_lat": 24.205, "center_lon": 82.675, "radius_m": 150.0, "speed_limit_kmh": 25.0},
        {"zone_id": "Z-MIN4-R1", "site_id": "SITE-MIN-04", "name": "Haul Loop 1", "kind": "haul_road", "center_lat": 24.203, "center_lon": 82.673, "radius_m": 400.0, "speed_limit_kmh": 40.0}
    ]

    machines = []
    # 10 excavators: EX-01..EX-10
    for i in range(1, 11):
        m_id = f"EX-{i:02d}"
        site = "SITE-CHN-01" if i in [1, 2, 7, 8] else ("SITE-BLR-02" if i in [3, 4] else "SITE-MIN-03")
        machines.append({
            "machine_id": m_id,
            "short_id": 100 + i,
            "site_id": site,
            "profile_id": "excavator_20t",
            "profile_version": 1,
            "machine_class": "excavator",
            "model_name": "Cat 320 GC",
            "year_of_manufacture": 2020 + (i % 4),
            "detail_level": "detailed",
            "data_origin": "demo_seed"
        })
    # 6 wheel loaders: WL-01..WL-06
    for i in range(1, 7):
        m_id = f"WL-{i:02d}"
        site = "SITE-CHN-01" if i in [1, 2] else ("SITE-BLR-02" if i in [3, 4] else "SITE-MIN-03")
        machines.append({
            "machine_id": m_id,
            "short_id": 200 + i,
            "site_id": site,
            "profile_id": "wheel_loader_950",
            "profile_version": 1,
            "machine_class": "wheel_loader",
            "model_name": "Cat 950 GC",
            "year_of_manufacture": 2019 + (i % 4),
            "detail_level": "detailed",
            "data_origin": "demo_seed"
        })
    # 8 haul trucks: HT-01..HT-08
    for i in range(1, 9):
        m_id = f"HT-{i:02d}"
        site = "SITE-MIN-03" if i in [1, 2, 3, 4, 5] else "SITE-MIN-04"
        machines.append({
            "machine_id": m_id,
            "short_id": 300 + i,
            "site_id": site,
            "profile_id": "haul_truck_90t",
            "profile_version": 1,
            "machine_class": "haul_truck",
            "model_name": "Cat 777G",
            "year_of_manufacture": 2018 + (i % 5),
            "detail_level": "detailed",
            "data_origin": "demo_seed"
        })
    # 76 status-only fleet machines: FL-001..FL-076
    for i in range(1, 77):
        m_id = f"FL-{i:03d}"
        site = sites[i % 4]["site_id"]
        m_class = "excavator" if i % 3 == 0 else ("wheel_loader" if i % 3 == 1 else "haul_truck")
        prof_id = f"{m_class}_20t" if m_class == "excavator" else (f"{m_class}_950" if m_class == "wheel_loader" else f"{m_class}_90t")
        machines.append({
            "machine_id": m_id,
            "short_id": 400 + i,
            "site_id": site,
            "profile_id": prof_id,
            "profile_version": 1,
            "machine_class": m_class,
            "model_name": f"Generic {m_class.title()}",
            "year_of_manufacture": 2017 + (i % 7),
            "detail_level": "status_only",
            "data_origin": "demo_seed"
        })

    def make_pin_hash(op_id, pin_str):
        salt = hashlib.sha256(f"salt:{op_id}".encode()).hexdigest()[:32]
        salt_bytes = bytes.fromhex(salt)
        h = hashlib.pbkdf2_hmac("sha256", pin_str.encode("utf-8"), salt_bytes, 20000, 32)
        return salt, h.hex()

    first_names = [
        "Ravi", "Kumar", "Senthil", "Amit", "Rajesh", "Vijay", "Manoj", "Suresh",
        "Dinesh", "Arun", "Vikas", "Pankaj", "Deepak", "Sunil", "Anil", "Sanjay",
        "Ramesh", "Ganesh", "Mahesh", "Naresh", "Karthik", "Pradeep", "Praveen", "Ashok",
        "Mukesh", "Rakesh", "Ajay", "Sachin", "Rahul", "Rohit", "Varun", "Naveen",
        "Satish", "Subhash", "Vinod", "Hemant", "Jitendra", "Dharmendra", "Gopal", "Harish",
        "Jagdish", "Kishore", "Lalit", "Mohan", "Nitin", "Om", "Pramod", "Santosh"
    ]

    # Operator roster. Skill level is NOT tied to machine class: every class has beginners,
    # intermediates and experts, experience ranges overlap between levels, and each operator's
    # home site matches the machines they run. Experience is given at the anchor date
    # (2026-09-22); hired_at is derived from it so the generator can compute experience per task date.
    # (op_id, class, site, skill, experience_months_at_anchor, language)
    roster = [
        # Excavator operators — Chennai (EX-01, 02, 07, 08)
        ("OP-0001", "excavator", "SITE-CHN-01", "beginner", 8, "ta"),
        ("OP-0002", "excavator", "SITE-CHN-01", "intermediate", 30, "en"),
        ("OP-0003", "excavator", "SITE-CHN-01", "expert", 110, "ta"),
        ("OP-0004", "excavator", "SITE-CHN-01", "intermediate", 22, "hi"),
        ("OP-0005", "excavator", "SITE-CHN-01", "beginner", 14, "en"),
        ("OP-0007", "excavator", "SITE-CHN-01", "beginner", 0, "en"),       # Ravi (demo)
        ("OP-0011", "excavator", "SITE-CHN-01", "expert", 96, "en"),        # Kumar (demo)
        ("OP-0012", "excavator", "SITE-CHN-01", "intermediate", 55, "ta"),
        # Excavator operators — Bengaluru (EX-03, 04)
        ("OP-0006", "excavator", "SITE-BLR-02", "expert", 70, "en"),
        ("OP-0008", "excavator", "SITE-BLR-02", "beginner", 5, "hi"),
        ("OP-0009", "excavator", "SITE-BLR-02", "intermediate", 40, "en"),
        ("OP-0010", "excavator", "SITE-BLR-02", "intermediate", 16, "hi"),
        # Excavator operators — Jharkhand pit (EX-05, 06, 09, 10)
        ("OP-0013", "excavator", "SITE-MIN-03", "beginner", 10, "hi"),
        ("OP-0014", "excavator", "SITE-MIN-03", "intermediate", 36, "hi"),
        ("OP-0015", "excavator", "SITE-MIN-03", "expert", 150, "hi"),
        ("OP-0016", "excavator", "SITE-MIN-03", "intermediate", 60, "en"),
        ("OP-0017", "excavator", "SITE-MIN-03", "expert", 58, "hi"),
        ("OP-0018", "excavator", "SITE-MIN-03", "beginner", 2, "hi"),
        ("OP-0019", "excavator", "SITE-MIN-03", "intermediate", 26, "en"),
        ("OP-0020", "excavator", "SITE-MIN-03", "expert", 84, "hi"),
        # Haul-truck operators — Jharkhand pit (HT-01..05)
        ("OP-0021", "haul_truck", "SITE-MIN-03", "expert", 132, "hi"),      # Senthil (demo)
        ("OP-0022", "haul_truck", "SITE-MIN-03", "beginner", 6, "hi"),
        ("OP-0023", "haul_truck", "SITE-MIN-03", "intermediate", 28, "hi"),
        ("OP-0024", "haul_truck", "SITE-MIN-03", "expert", 90, "en"),
        ("OP-0025", "haul_truck", "SITE-MIN-03", "intermediate", 44, "hi"),
        ("OP-0026", "haul_truck", "SITE-MIN-03", "beginner", 11, "hi"),
        ("OP-0027", "haul_truck", "SITE-MIN-03", "intermediate", 19, "en"),
        ("OP-0028", "haul_truck", "SITE-MIN-03", "expert", 65, "hi"),
        ("OP-0029", "haul_truck", "SITE-MIN-03", "beginner", 3, "hi"),
        ("OP-0030", "haul_truck", "SITE-MIN-03", "intermediate", 50, "hi"),
        # Haul-truck operators — Singrauli pit (HT-06..08)
        ("OP-0031", "haul_truck", "SITE-MIN-04", "intermediate", 33, "hi"),
        ("OP-0032", "haul_truck", "SITE-MIN-04", "beginner", 9, "hi"),
        ("OP-0033", "haul_truck", "SITE-MIN-04", "expert", 120, "hi"),
        ("OP-0034", "haul_truck", "SITE-MIN-04", "intermediate", 24, "en"),
        ("OP-0035", "haul_truck", "SITE-MIN-04", "expert", 62, "hi"),
        ("OP-0036", "haul_truck", "SITE-MIN-04", "beginner", 15, "hi"),
        # Wheel-loader operators (profile-only class: no generated tasks)
        ("OP-0037", "wheel_loader", "SITE-CHN-01", "beginner", 4, "ta"),
        ("OP-0038", "wheel_loader", "SITE-CHN-01", "intermediate", 30, "en"),
        ("OP-0039", "wheel_loader", "SITE-CHN-01", "expert", 80, "ta"),
        ("OP-0040", "wheel_loader", "SITE-CHN-01", "intermediate", 20, "en"),
        ("OP-0041", "wheel_loader", "SITE-BLR-02", "beginner", 12, "en"),
        ("OP-0042", "wheel_loader", "SITE-BLR-02", "expert", 100, "hi"),
        ("OP-0043", "wheel_loader", "SITE-BLR-02", "intermediate", 45, "en"),
        ("OP-0044", "wheel_loader", "SITE-BLR-02", "beginner", 7, "hi"),
        ("OP-0045", "wheel_loader", "SITE-MIN-03", "intermediate", 27, "hi"),
        ("OP-0046", "wheel_loader", "SITE-MIN-03", "expert", 70, "hi"),
        ("OP-0047", "wheel_loader", "SITE-MIN-03", "beginner", 1, "hi"),
        ("OP-0048", "wheel_loader", "SITE-MIN-03", "intermediate", 38, "en"),
    ]
    demo_pins = {"OP-0007": "1234", "OP-0011": "2468", "OP-0021": "7777"}
    demo_names = {"OP-0007": "Ravi", "OP-0011": "Kumar", "OP-0021": "Senthil"}
    demo_hired = {"OP-0007": "2026-09-02", "OP-0011": "2018-09-15", "OP-0021": "2015-09-10"}

    def hired_from_months(op_num: int, months: int) -> str:
        # anchor 2026-09-22 minus `months` whole months; day varies per operator (1..28)
        total = 2026 * 12 + 8 - months          # 0-based month index of September 2026 is 8
        year, month0 = divmod(total, 12)
        day = 1 + (op_num * 7) % 22        # always on or before the 22nd, so months at anchor == `months`
        return f"{year:04d}-{month0 + 1:02d}-{day:02d}"

    operators = []
    for op_id, reg_class, site, skill, exp, lang in sorted(roster):
        n = int(op_id[3:])
        name = demo_names.get(op_id, first_names[(n - 1) % len(first_names)])
        pin = demo_pins.get(op_id, f"{1000 + n:04d}")
        salt, pin_h = make_pin_hash(op_id, pin)
        operators.append({
            "operator_id": op_id,
            "display_name": name,
            "language": lang,
            "skill_level": skill,
            "experience_months": exp,
            "hired_at": demo_hired.get(op_id, hired_from_months(n, exp)),
            "site_id": site,
            "regular_machine_class": reg_class,
            "pin_salt": salt,
            "pin_hash": pin_h,
            "pin_iterations": 20000,
            "data_origin": "demo_seed"
        })
    assert len(operators) == 48 and len({o["operator_id"] for o in operators}) == 48

    console_users = [
        {
            "username": "sup.priya",
            "display_name": "Priya Sharma",
            "role": "supervisor",
            "site_ids": ["SITE-CHN-01", "SITE-BLR-02", "SITE-MIN-03", "SITE-MIN-04"],
            "password_hash": ph.hash("Priya-Demo-2026")
        },
        {
            "username": "trn.arjun",
            "display_name": "Arjun Patel",
            "role": "trainer",
            "site_ids": ["SITE-CHN-01", "SITE-BLR-02", "SITE-MIN-03", "SITE-MIN-04"],
            "password_hash": ph.hash("Arjun-Demo-2026")
        },
        {
            "username": "saf.meena",
            "display_name": "Meena Iyer",
            "role": "safety",
            "site_ids": ["SITE-CHN-01", "SITE-BLR-02", "SITE-MIN-03", "SITE-MIN-04"],
            "password_hash": ph.hash("Meena-Demo-2026")
        },
        {
            "username": "mec.dinesh",
            "display_name": "Dinesh Verma",
            "role": "mechanic",
            "site_ids": ["SITE-CHN-01", "SITE-BLR-02", "SITE-MIN-03", "SITE-MIN-04"],
            "password_hash": ph.hash("Dinesh-Demo-2026")
        }
    ]

    pairing_codes = [
        {"code": "100007", "machine_id": "EX-07", "reusable": True, "expires_in_days": 365},
        {"code": "300003", "machine_id": "HT-03", "reusable": True, "expires_in_days": 365},
        {"code": "200002", "machine_id": "WL-02", "reusable": True, "expires_in_days": 365}
    ]

    assignments = [
        {
            "task_id": "T-20260923-EX07-1",
            "site_id": "SITE-CHN-01",
            "machine_id": "EX-07",
            "operator_id": "OP-0007",
            "task_type": "trenching",
            "zone_id": "Z-CHN-TR1",
            "location_text": "Trench Area T1 East",
            "quantity": 40.0,
            "unit": "m",
            "material": "clay",
            "priority": 1,
            "completion_criterion": "40 m trench, 1.2 m deep, spoil on east side",
            "planner_minutes": 30.0,
            "planned_day_offset": 0,
            "planned_start_local": "13:10",
            "planned_start_window_min": 15,
            "sequence": 1,
            "source": "seed"
        },
        {
            "task_id": "T-20260923-EX07-2",
            "site_id": "SITE-CHN-01",
            "machine_id": "EX-07",
            "operator_id": "OP-0007",
            "task_type": "truck_loading",
            "zone_id": "Z-CHN-LB2",
            "location_text": "Loading Bay 2",
            "quantity": 60.0,
            "unit": "m3",
            "material": "clay",
            "priority": 2,
            "completion_criterion": "Load 5 articulated trucks with clay",
            "planner_minutes": 25.0,
            "planned_day_offset": 0,
            "planned_start_local": "14:10",
            "planned_start_window_min": 15,
            "sequence": 2,
            "source": "seed"
        },
        {
            "task_id": "T-20260923-EX07-3",
            "site_id": "SITE-CHN-01",
            "machine_id": "EX-07",
            "operator_id": "OP-0007",
            "task_type": "trenching",
            "zone_id": "Z-CHN-TR2",
            "location_text": "Trench Area T2",
            "quantity": 25.0,
            "unit": "m",
            "material": "clay",
            "priority": 2,
            "completion_criterion": "25 m utility trench",
            "planner_minutes": 20.0,
            "planned_day_offset": 0,
            "planned_start_local": None,
            "planned_start_window_min": 15,
            "sequence": 3,
            "source": "seed"
        },
        {
            "task_id": "T-20260923-HT03-1",
            "site_id": "SITE-MIN-03",
            "machine_id": "HT-03",
            "operator_id": "OP-0021",
            "task_type": "haul_overburden",
            "zone_id": "Z-MIN-SH1",
            "location_text": "Shovel 1 to Dump Area",
            "quantity": 1600.0,
            "unit": "t",
            "material": "overburden",
            "priority": 1,
            "completion_criterion": "Haul 18 loads to overburden dump",
            "planner_minutes": 240.0,
            "planned_day_offset": 0,
            "planned_start_local": "22:00",
            "planned_start_window_min": 15,
            "sequence": 1,
            "source": "seed"
        }
    ]

    handovers = [
        {
            "handover_id": "ho-seed-ex07-prev",
            "machine_id": "EX-07",
            "from_operator_id": "OP-0011",
            "created_offset_min": -480,
            "items": [
                {
                    "item_id": "hi-seed-ex07-blocked",
                    "item_type": "blocked_task",
                    "text": "Trench T2 blocked by utility mark — wait for supervisor clearance",
                    "audiences": ["next_operator", "site"],
                    "status": "open",
                    "task_id": "T-20260923-EX07-3",
                    "incident_id": None
                },
                {
                    "item_id": "hi-seed-ex07-defect",
                    "item_type": "defect",
                    "text": "Hydraulic oil temperature high at 02:10 — watch the gauge",
                    "audiences": ["next_operator", "site"],
                    "status": "open",
                    "task_id": None,
                    "incident_id": "inc-seed-ex07-hyd"
                }
            ]
        }
    ]

    forecast = []
    # 48 hours for each site
    for site in sites:
        s_id = site["site_id"]
        for h in range(-12, 36):
            if s_id == "SITE-CHN-01" and h >= 6: # Rain starting in afternoon
                weather = "rain"
                vis = "moderate"
                vis_m = 3500.0
                precip = 4.2
                temp = 29.5
                wind = 18.0
            elif s_id == "SITE-MIN-03":
                weather = "dusty"
                vis = "moderate"
                vis_m = 4000.0
                precip = 0.0
                temp = 34.0
                wind = 22.0
            else:
                weather = "clear"
                vis = "good"
                vis_m = 10000.0
                precip = 0.0
                temp = 31.0
                wind = 12.0

            forecast.append({
                "site_id": s_id,
                "hour_offset": h,
                "weather": weather,
                "visibility": vis,
                "visibility_m": vis_m,
                "temp_c": temp,
                "heat_index_c": temp + 3.0,
                "wind_kmh": wind,
                "precipitation_mm": precip,
                "source": "seed"
            })

    seed_data = {
        "seed_version": "1.0.0",
        "sites": sites,
        "zones": zones,
        "machines": machines,
        "operators": operators,
        "console_users": console_users,
        "pairing_codes": pairing_codes,
        "assignments": assignments,
        "handovers": handovers,
        "forecast": forecast
    }

    repo_root = Path(__file__).resolve().parent.parent.parent
    out_path = repo_root / "packages" / "content" / "seed" / "demo_seed.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, indent=2)
    print(f"Generated {out_path} with {len(machines)} machines, {len(operators)} operators, {len(sites)} sites, {len(zones)} zones.")

if __name__ == "__main__":
    make_seed()
