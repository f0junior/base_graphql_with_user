from fastapi import Request, Response

from app.core.database import get_session
from app.core.redis import redis_manager
from app.graphql.context import Context


async def get_context(request: Request, response: Response):
    await redis_manager.connect()
    async with get_session() as session:
        yield Context(
            session=session,
            redis=redis_manager.get_client(),
            request=request,
            response=response,
        )
