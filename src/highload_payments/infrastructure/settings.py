from dataclasses import dataclass
import os
from urllib.parse import quote_plus


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
    max_attempts: int
    retry_base_seconds: int
    retry_max_seconds: int
    retry_jitter_seconds: float


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
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    name = os.getenv("POSTGRES_DB", "payments")

    dsn = (
        f"postgresql+asyncpg://"
        f"{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )
    config = DbConfig(
        dsn=dsn,
        pool_size=int(os.getenv("POSTGRES_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("POSTGRES_MAX_OVERFLOW", "20")),
    )
    if not user:
        raise ValueError("POSTGRES_USER must not be empty")
    if not host:
        raise ValueError("POSTGRES_HOST must not be empty")
    if not name:
        raise ValueError("POSTGRES_DB must not be empty")
    if port < 1 or port > 65535:
        raise ValueError("POSTGRES_PORT must be in range 1..65535")
    if config.pool_size < 1:
        raise ValueError("POSTGRES_POOL_SIZE must be >= 1")
    if config.max_overflow < 0:
        raise ValueError("POSTGRES_MAX_OVERFLOW must be >= 0")
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
        max_attempts=int(os.getenv("WORKER_MAX_ATTEMPTS", "10")),
        retry_base_seconds=int(os.getenv("WORKER_RETRY_BASE_SECONDS", "1")),
        retry_max_seconds=int(os.getenv("WORKER_RETRY_MAX_SECONDS", "60")),
        retry_jitter_seconds=float(os.getenv("WORKER_RETRY_JITTER_SECONDS", "0.25")),
    )
    if config.batch_size < 1:
        raise ValueError("WORKER_BATCH_SIZE must be >= 1")
    if config.poll_interval_seconds <= 0:
        raise ValueError("WORKER_POLL_INTERVAL_SECONDS must be > 0")
    if config.max_attempts < 1:
        raise ValueError("WORKER_MAX_ATTEMPTS must be >= 1")
    if config.retry_base_seconds < 1:
        raise ValueError("WORKER_RETRY_BASE_SECONDS must be >= 1")
    if config.retry_max_seconds < 1:
        raise ValueError("WORKER_RETRY_MAX_SECONDS must be >= 1")
    if config.retry_max_seconds < config.retry_base_seconds:
        raise ValueError("WORKER_RETRY_MAX_SECONDS must be >= WORKER_RETRY_BASE_SECONDS")
    if config.retry_jitter_seconds < 0:
        raise ValueError("WORKER_RETRY_JITTER_SECONDS must be >= 0")
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
