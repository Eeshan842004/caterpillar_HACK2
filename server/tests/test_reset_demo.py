"""`reset-demo` (§5.2 deletion/cascade, §10.5; TC-60): empties dynamic tables, deletes uploads, re-seeds;
refused unless DEMO_MODE=true."""

import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shiftmate import cli
from shiftmate.config import settings
from shiftmate.db import Base
from shiftmate.models import ChangeLog, Device, Machine
from shiftmate.seed import reset_demo, seed_database


def test_reset_empties_tables_and_uploads_then_reseeds(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path / "reset.db").as_posix())
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        seeded = seed_database(db)
        assert seed_database(db) == seeded  # TC-60: seeding twice gives identical counts
        db.add(Device(label="stale", machine_id=db.query(Machine).first().machine_id))
        db.commit()
        stray = settings.upload_path / "voice_notes" / "2026" / "09" / "old.m4a"
        stray.parent.mkdir(parents=True, exist_ok=True)
        stray.write_bytes(b"x")

        assert reset_demo(db) == seeded
        assert db.query(Device).count() == 0
        assert {c.change_type for c in db.query(ChangeLog).all()} == {"model.published"}
        assert not stray.exists() and list(settings.upload_path.iterdir()) == []
    finally:
        db.close()
        engine.dispose()


def test_reset_is_refused_outside_demo_mode(monkeypatch, capsys):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(sys, "argv", ["shiftmate-cli", "reset-demo", "--yes"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1 and "DEMO_MODE=true" in capsys.readouterr().out
