import orjson
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from highload_payments.infrastructure.settings import DbConfig


@dataclass(frozen=True, slots=True)
class DbRuntime:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]

    async def dispose(self) -> None:
        await self.engine.dispose()


def create_db_runtime(db_config: DbConfig) -> DbRuntime:
    engine = create_async_engine(
        db_config.dsn,
        pool_size=db_config.pool_size,
        max_overflow=db_config.max_overflow,
        pool_pre_ping=True,
        json_serializer=lambda data: orjson.dumps(data).decode(),
        json_deserializer=orjson.loads,
    )
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
    )
    return DbRuntime(engine=engine, session_factory=session_factory)
