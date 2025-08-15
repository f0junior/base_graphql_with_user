from typing import AsyncGenerator

import pytest
from fastapi import Request, Response
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.graphql.context import Context
from app.main import app


@pytest.fixture
async def graphql_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        try:
            yield client
        finally:
            client.cookies.clear()
            client.headers.clear()


@pytest.fixture
async def graphql_context(
    async_session: AsyncSession, async_redis: Redis
) -> AsyncGenerator[Context, None]:
    request = Request(scope={"type": "http"})
    response = Response()

    yield Context(
        session=async_session,
        redis=async_redis,
        request=request,
        response=response,
    )
