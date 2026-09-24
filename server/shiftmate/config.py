from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = "sqlite:///./var/shiftmate.db"
    TEST_DATABASE_URL: str = "sqlite:///:memory:"
    # Required, from the environment / .env only (§9.4). Generate with:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    DEVICE_SECRET_MASTER_KEY: str
    DEMO_MODE: bool = False
    CONSOLE_COOKIE_SECURE: bool = False
    SESSION_TTL_HOURS: int = 12
    CORS_ORIGINS: str = "http://localhost:8081,http://localhost:5173"
    CONTENT_DIR: str = "../packages/content"
    UPLOAD_DIR: str = "./var/uploads"
    AI_ENABLED: bool = False
    ANTHROPIC_API_KEY: str | None = None
    AI_MODEL: str = "claude-haiku-4-5"
    AI_DEVICE_TIMEOUT_S: float = 1.5
    AI_CONSOLE_TIMEOUT_S: float = 20.0
    LORA_GATEWAY_TOKEN: str = "replace-with-random-token"
    SMS_CONTACTS: str = ""
    FORECAST_ENABLED: bool = False
    FORECAST_POLL_MINUTES: int = 60
    FLEET_SIM_ENABLED: bool = False
    ISOFOREST_ENABLED: bool = False
    LOG_LEVEL: str = "info"

    @field_validator("DEVICE_SECRET_MASTER_KEY")
    @classmethod
    def _check_master_key(cls, value: str) -> str:
        try:
            raw = bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError("DEVICE_SECRET_MASTER_KEY must be 64 hex characters (see .env.example)") from exc
        if len(raw) != 32:
            raise ValueError("DEVICE_SECRET_MASTER_KEY must be 64 hex characters (32 bytes)")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def content_path(self) -> Path:
        p = Path(self.CONTENT_DIR)
        if p.is_absolute() and p.exists():
            return p
        if (Path.cwd() / self.CONTENT_DIR).exists():
            return (Path.cwd() / self.CONTENT_DIR).resolve()
        if (Path.cwd() / "packages" / "content").exists():
            return (Path.cwd() / "packages" / "content").resolve()
        repo_root = Path(__file__).resolve().parents[2]
        if (repo_root / "packages" / "content").exists():
            return (repo_root / "packages" / "content").resolve()
        server_dir = Path(__file__).resolve().parents[1]
        return (server_dir / self.CONTENT_DIR).resolve()

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        if not p.is_absolute():
            server_dir = Path(__file__).resolve().parents[1]
            p = (server_dir / self.UPLOAD_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
