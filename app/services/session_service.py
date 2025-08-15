import json
from uuid import UUID, uuid4

from redis.asyncio import Redis

from app.schemas.user_schema import UserRead


class SessionService:
    TIME_TO_SESSION = 90 * 60  # 1h30min

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    def _key_for_session(self, session_id: UUID) -> str:
        return f"session:{session_id}"

    async def create_session(self, data: UserRead) -> UUID:
        session_id = uuid4()
        await self.redis.setex(
            self._key_for_session(session_id),
            self.TIME_TO_SESSION,
            json.dumps(data.model_dump(mode="json")),
        )

        return session_id

    async def get_user_id_from_session(
        self, session_id: UUID
    ) -> UserRead | None:
        key = self._key_for_session(session_id)
        session_data = await self.redis.get(key)

        if not session_data:
            return None

        await self.redis.expire(key, self.TIME_TO_SESSION)

        user_data = json.loads(session_data)
        return UserRead.model_validate(user_data)

    async def delete_session(self, session_id: UUID) -> None:
        key = self._key_for_session(session_id)
        if await self.redis.exists(key):
            await self.redis.delete(key)
