from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    db_dsn: str
    nats_servers: str
    webhook_timeout_seconds: float
    outbox_batch_size: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "highload-payments"),
            db_dsn=os.getenv("DB_DSN", "postgresql+asyncpg://postgres:postgres@localhost:5432/payments"),
            nats_servers=os.getenv("NATS_SERVERS", "nats://localhost:4222"),
            webhook_timeout_seconds=float(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "3.0")),
            outbox_batch_size=int(os.getenv("OUTBOX_BATCH_SIZE", "100")),
        )
