import asyncio
import os
from typing import AsyncGenerator

import asyncpg
import pytest
from dotenv import load_dotenv
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401
from app.core.redis import redis_manager
from app.models.base_model import Base

# ruff: noqa: E402

ENV = os.getenv("ENV", "test")
load_dotenv(f".env.{ENV}", override=True)

from app.core.settings import settings

DATABASE_URL = settings.database_url_async


async def wait_for_postgres(retries=10, delay=2):
    for attempt in range(1, retries + 1):
        try:
            print(f"Esperando Postgres... Tentativa {attempt}/{retries}")
            conn = await asyncpg.connect(
                user=settings.user,
                password=settings.password,
                database=settings.dbname,
                host=settings.host,
                port=settings.port,
            )
            await conn.close()
            print("✅ Postgres está disponível!")
            return
        except Exception as e:
            print(f"❌ Falha na conexão: {e}")
            await asyncio.sleep(delay)
    raise RuntimeError(
        "Postgres não está disponível após múltiplas tentativas."
    )


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def wait_for_postgres_fixture():
    """Espera o banco estar pronto antes de começar os testes"""
    await wait_for_postgres()


@pytest.fixture(scope="session")
async def engine():
    async_engine = create_async_engine(
        f"{DATABASE_URL}?statement_cache_size=0",
        future=True,
        connect_args={"statement_cache_size": 0},
    )
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield async_engine
    finally:
        await async_engine.dispose()


@pytest.fixture(autouse=True)
async def clear_database(engine: AsyncEngine):
    """Limpa todas as tabelas antes de cada teste, preservando o schema"""
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def async_session(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Cria uma sessão nova para cada teste"""
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
async def async_redis() -> AsyncGenerator[Redis, None]:
    async with redis_manager.lifespan() as client:
        yield client
