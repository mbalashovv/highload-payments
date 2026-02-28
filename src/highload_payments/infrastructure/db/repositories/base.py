from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
