import pytest
from sqlalchemy import text


@pytest.mark.anyio
@pytest.mark.order(1)
async def test_database_connection(async_session):
    result = await async_session.execute(text("SELECT 1"))
    assert result.scalar() == 1
