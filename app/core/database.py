from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import settings

# Engine assíncrona com o driver asyncpg
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.debug,
)

# Criador de sessões assíncronas
async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Fornece uma sessão de banco de dados async para uso com FastAPI."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
