import argparse
import sys
from datetime import datetime, timedelta, timezone

from shiftmate.config import settings
from shiftmate.db import Base, SessionLocal, engine
from shiftmate.models import Device, PairingCode
from shiftmate.security.passwords import hash_password as calc_hash_password
from shiftmate.security.pin import compute_pin_salt
from shiftmate.security.pin import hash_pin as calc_hash_pin
from shiftmate.seed import seed_database


def main():
    parser = argparse.ArgumentParser(prog="shiftmate-cli", description="ShiftMate CLI administration tool")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # seed
    subparsers.add_parser("seed", help="Seed database with demo seed and machine profiles")

    # reset-demo
    reset_parser = subparsers.add_parser("reset-demo", help="Reset and re-seed the demo database")
    reset_parser.add_argument("--yes", action="store_true", help="Confirm database reset")

    # hash-pin
    pin_parser = subparsers.add_parser("hash-pin", help="Compute PBKDF2 hash for a PIN")
    pin_parser.add_argument("--pin", required=True, help="4-6 digit PIN")
    pin_parser.add_argument("--salt", help="32-hex salt (generated if omitted)")
    pin_parser.add_argument("--operator-id", help="Operator ID for deterministic salt")

    # hash-password
    pw_parser = subparsers.add_parser("hash-password", help="Compute Argon2 hash for a password")
    pw_parser.add_argument("--password", required=True, help="Console user password")

    # create-pairing-code
    code_parser = subparsers.add_parser("create-pairing-code", help="Create a machine pairing code")
    code_parser.add_argument("--machine", required=True, help="Machine ID (e.g. EX-07)")
    code_parser.add_argument("--code", help="6-digit code (random if omitted)")
    code_parser.add_argument("--reusable", action="store_true", help="Whether the code can be reused")
    code_parser.add_argument("--days", type=int, default=30, help="Validity in days")

    # revoke-device
    revoke_parser = subparsers.add_parser("revoke-device", help="Revoke a paired device")
    revoke_parser.add_argument("--device-id", required=True, help="Device UUID")

    # doctor
    subparsers.add_parser("doctor", help="Check database connectivity and integrity")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "hash-pin":
        salt = args.salt
        if not salt:
            if args.operator_id:
                salt = compute_pin_salt(args.operator_id)
            else:
                salt = compute_pin_salt("OP-DEFAULT")
        h = calc_hash_pin(args.pin, salt)
        print(f"Salt: {salt}")
        print(f"Hash: {h}")

    elif args.command == "hash-password":
        h = calc_hash_password(args.password)
        print(f"Argon2 hash: {h}")

    elif args.command == "seed":
        Base.metadata.create_all(bind=engine)
        counts = seed_database()
        print("Database seeded:", counts)

    elif args.command == "reset-demo":
        if not settings.DEMO_MODE:
            print("Error: reset-demo is only allowed when DEMO_MODE=true.")
            sys.exit(1)
        if not args.yes:
            print("Please confirm reset with --yes")
            sys.exit(1)
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        counts = seed_database()
        print("Database reset and re-seeded:", counts)

    elif args.command == "create-pairing-code":
        import secrets
        code = args.code or f"{secrets.randbelow(900000) + 100000}"
        db = SessionLocal()
        try:
            expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=args.days)
            pc = PairingCode(
                code=code,
                machine_id=args.machine,
                reusable=args.reusable,
                expires_at=expires,
            )
            db.merge(pc)
            db.commit()
            print(f"Created pairing code {code} for machine {args.machine} (reusable={args.reusable}, expires={expires})")
        finally:
            db.close()

    elif args.command == "revoke-device":
        db = SessionLocal()
        try:
            dev = db.query(Device).filter(Device.device_id == args.device_id).first()
            if not dev:
                print(f"Device {args.device_id} not found.")
                sys.exit(1)
            dev.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            print(f"Device {args.device_id} has been revoked.")
        finally:
            db.close()

    elif args.command == "doctor":
        db = SessionLocal()
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            print("Database connection: OK")
            print("Content path:", settings.content_path)
            print("Upload path:", settings.upload_path)
            print("Demo mode:", settings.DEMO_MODE)
        except Exception as e:
            print("Doctor check failed:", e)
            sys.exit(1)
        finally:
            db.close()


if __name__ == "__main__":
    main()
