import json
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from faker import Faker
from pydantic import ValidationError

from app.schemas.user_schema import UserRead
from app.services.session_service import SessionService

faker = Faker()


@pytest.mark.anyio
class TestSessionService:
    @pytest.fixture
    def redis_mock(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, redis_mock) -> SessionService:
        svc = SessionService(redis_mock)
        svc.redis = redis_mock
        return svc

    async def test_key_for_session_success(self, service: SessionService):
        session_id = faker.uuid4(cast_to=None)
        key = service._key_for_session(session_id)
        assert key == f"session:{session_id}"

    async def test_create_session_success(
        self, redis_mock, service: SessionService
    ):
        user = UserRead(
            id=faker.uuid4(cast_to=None),
            name=faker.name(),
            username=faker.first_name(),
            email=faker.email(),
            is_master=False,
        )

        redis_mock.setex = AsyncMock()

        session_id = await service.create_session(user)

        assert isinstance(session_id, UUID)
        redis_mock.setex.assert_awaited_once_with(
            service._key_for_session(session_id),
            service.TIME_TO_SESSION,
            json.dumps(user.model_dump(mode="json")),
        )

    async def test_get_user_id_from_session_success(
        self, redis_mock, service: SessionService
    ):
        user = UserRead(
            id=faker.uuid4(cast_to=None),
            name=faker.name(),
            username=faker.first_name(),
            email=faker.email(),
            is_master=False,
        )

        redis_mock.get = AsyncMock(
            return_value=json.dumps(user.model_dump(mode="json"))
        )

        redis_mock.expire = AsyncMock()

        session_id = faker.uuid4(cast_to=None)
        key = service._key_for_session(session_id)
        result = await service.get_user_id_from_session(session_id)

        assert isinstance(result, UserRead)
        assert result.id == user.id
        redis_mock.get.assert_awaited_once_with(key)
        redis_mock.expire.assert_awaited_once_with(
            key, service.TIME_TO_SESSION
        )

    async def test_get_user_id_from_session_failure_not_found(
        self, redis_mock, service: SessionService
    ):
        redis_mock.get = AsyncMock(return_value=None)

        session_id = faker.uuid4(cast_to=None)

        result = await service.get_user_id_from_session(session_id)

        assert result is None
        redis_mock.get.assert_awaited_once_with(
            service._key_for_session(session_id)
        )
        redis_mock.expire.assert_not_awaited()

    async def test_get_user_id_from_session_failure_invalid_schema(
        self, redis_mock, service: SessionService
    ):
        redis_mock.get = AsyncMock(
            return_value=json.dumps({"username": "ash"})
        )

        session_id = faker.uuid4(cast_to=None)

        with pytest.raises(ValidationError):
            await service.get_user_id_from_session(session_id)

        redis_mock.get.assert_awaited_once_with(
            service._key_for_session(session_id)
        )

    async def test_delete_session_success(
        self, redis_mock, service: SessionService
    ):
        redis_mock.delete = AsyncMock()
        redis_mock.exists = AsyncMock(return_value=True)

        session_id = faker.uuid4(cast_to=None)
        key = service._key_for_session(session_id)

        await service.delete_session(session_id)

        redis_mock.exists.assert_awaited_once_with(key)
        redis_mock.delete.assert_awaited_once_with(key)

    async def test_delete_session_failure_expired(
        self, redis_mock, service: SessionService
    ):
        redis_mock.delete = AsyncMock()
        redis_mock.exists = AsyncMock(return_value=False)

        session_id = faker.uuid4(cast_to=None)

        await service.delete_session(session_id)

        redis_mock.exists.assert_awaited_once_with(
            service._key_for_session(session_id)
        )
        redis_mock.delete.assert_not_awaited()
