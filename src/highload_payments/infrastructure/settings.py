from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class CommonConfig:
    app_name: str
    environment: str
    log_level: str


@dataclass(frozen=True, slots=True)
class DbConfig:
    dsn: str
    pool_size: int
    max_overflow: int


@dataclass(frozen=True, slots=True)
class NatsConfig:
    servers: tuple[str, ...]
    stream_name: str
    outbox_subject: str
    consumer_durable: str


@dataclass(frozen=True, slots=True)
class ApiConfig:
    host: str
    port: int


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    batch_size: int
    poll_interval_seconds: float


@dataclass(frozen=True, slots=True)
class DispatcherConfig:
    webhook_timeout_seconds: float
    poll_interval_seconds: float
    max_retries: int


@dataclass(frozen=True, slots=True)
class ApiSettings:
    common: CommonConfig
    db: DbConfig
    nats: NatsConfig
    api: ApiConfig


@dataclass(frozen=True, slots=True)
class WorkerSettings:
    common: CommonConfig
    db: DbConfig
    nats: NatsConfig
    worker: WorkerConfig


@dataclass(frozen=True, slots=True)
class DispatcherSettings:
    common: CommonConfig
    db: DbConfig
    nats: NatsConfig
    dispatcher: DispatcherConfig


def load_api_settings() -> ApiSettings:
    return ApiSettings(
        common=_load_common_config(),
        db=load_db_config(),
        nats=_load_nats_config(),
        api=_load_api_config(),
    )


def load_worker_settings() -> WorkerSettings:
    return WorkerSettings(
        common=_load_common_config(),
        db=load_db_config(),
        nats=_load_nats_config(),
        worker=_load_worker_config(),
    )


def load_dispatcher_settings() -> DispatcherSettings:
    return DispatcherSettings(
        common=_load_common_config(),
        db=load_db_config(),
        nats=_load_nats_config(),
        dispatcher=_load_dispatcher_config(),
    )


def _load_common_config() -> CommonConfig:
    return CommonConfig(
        app_name=os.getenv("APP_NAME", "highload-payments"),
        environment=os.getenv("APP_ENV", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


def load_db_config() -> DbConfig:
    config = DbConfig(
        dsn=os.getenv(
            "DB_DSN",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/payments",
        ),
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    )
    if not config.dsn:
        raise ValueError("DB_DSN must not be empty")
    if config.pool_size < 1:
        raise ValueError("DB_POOL_SIZE must be >= 1")
    if config.max_overflow < 0:
        raise ValueError("DB_MAX_OVERFLOW must be >= 0")
    return config


def _load_nats_config() -> NatsConfig:
    servers_raw = os.getenv("NATS_SERVERS", "nats://localhost:4222")
    servers = tuple(item.strip() for item in servers_raw.split(",") if item.strip())
    if not servers:
        raise ValueError("NATS_SERVERS must contain at least one server")

    return NatsConfig(
        servers=servers,
        stream_name=os.getenv("NATS_STREAM_NAME", "payments"),
        outbox_subject=os.getenv("NATS_OUTBOX_SUBJECT", "payments.outbox"),
        consumer_durable=os.getenv("NATS_CONSUMER_DURABLE", "dispatcher-webhooks"),
    )


def _load_api_config() -> ApiConfig:
    config = ApiConfig(
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8080")),
    )
    if config.port < 1 or config.port > 65535:
        raise ValueError("API_PORT must be in range 1..65535")
    return config


def _load_worker_config() -> WorkerConfig:
    config = WorkerConfig(
        batch_size=int(os.getenv("WORKER_BATCH_SIZE", "100")),
        poll_interval_seconds=float(os.getenv("WORKER_POLL_INTERVAL_SECONDS", "0.5")),
    )
    if config.batch_size < 1:
        raise ValueError("WORKER_BATCH_SIZE must be >= 1")
    if config.poll_interval_seconds <= 0:
        raise ValueError("WORKER_POLL_INTERVAL_SECONDS must be > 0")
    return config


def _load_dispatcher_config() -> DispatcherConfig:
    config = DispatcherConfig(
        webhook_timeout_seconds=float(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "3.0")),
        poll_interval_seconds=float(os.getenv("DISPATCHER_POLL_INTERVAL_SECONDS", "1.0")),
        max_retries=int(os.getenv("DISPATCHER_MAX_RETRIES", "8")),
    )
    if config.webhook_timeout_seconds <= 0:
        raise ValueError("WEBHOOK_TIMEOUT_SECONDS must be > 0")
    if config.poll_interval_seconds <= 0:
        raise ValueError("DISPATCHER_POLL_INTERVAL_SECONDS must be > 0")
    if config.max_retries < 0:
        raise ValueError("DISPATCHER_MAX_RETRIES must be >= 0")
    return config
