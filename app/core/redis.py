from contextlib import asynccontextmanager

from redis.asyncio import Redis


class RedisManager:
    def __init__(
        self, url: str = "redis://localhost", max_connections: int = 10
    ) -> None:
        self._url = url
        self._max_connections = max_connections
        self._client: Redis | None = None

    def get_client(self) -> Redis:
        if not self._client:
            raise RuntimeError(
                "Redis client not connected. Call connect() first."
            )
        return self._client

    async def connect(self):
        if not self._client:
            self._client = Redis.from_url(
                self._url,
                decode_responses=True,
                max_connections=self._max_connections,
            )

        await self._client.ping()

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    @asynccontextmanager
    async def lifespan(self):
        await self.connect()
        try:
            yield self.get_client()
        finally:
            await self.close()


redis_manager = RedisManager()
