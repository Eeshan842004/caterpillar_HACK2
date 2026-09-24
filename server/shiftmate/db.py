from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from shiftmate.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./var/"):
    server_dir = Path(__file__).resolve().parents[1]
    db_file = (server_dir / "var" / db_url.replace("sqlite:///./var/", "")).resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{db_file}"
elif db_url.startswith("sqlite:///./"):
    # Ensure local directory exists
    rel_path = db_url.replace("sqlite:///./", "")
    p = Path(rel_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)

engine_kwargs = {}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(db_url, **engine_kwargs)

if db_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record) -> None:
        """WAL + busy timeout: the single-worker demo server writes from request threads and background tasks
        (fleet simulator, forecast poller) at once; without these SQLite raises "database is locked"."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
