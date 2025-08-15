from datetime import datetime
from uuid import UUID

import pytest
from faker import Faker
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import UserModel

faker = Faker()


@pytest.mark.anyio
class TestUserModel:
    @pytest.fixture(autouse=True)
    def setup(self, async_session: AsyncSession):
        self.db = async_session

    @pytest.fixture(autouse=True)
    async def cleanup(self, async_session: AsyncSession):
        yield
        await async_session.rollback()

    def _make_data(self, **kwargs):
        data = {
            "name": faker.name(),
            "username": faker.first_name(),
            "email": faker.email(),
            "hashed_password": faker.sha256(),
            "is_master": False,
        }
        data.update(**kwargs)

        return data

    async def _assert_commit_raises_integrity(self):
        with pytest.raises(IntegrityError):
            await self.db.commit()

    async def test_create_user_success(self):
        user = UserModel(**self._make_data())

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, UUID)

        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

        assert user.updated_at is not None
        assert isinstance(user.updated_at, datetime)

    async def test_create_user_failure_dup_email(self):
        email = faker.email()
        user1 = UserModel(**self._make_data(email=email))
        user2 = UserModel(**self._make_data(email=email))

        self.db.add(user1)
        await self.db.commit()

        self.db.add(user2)
        await self._assert_commit_raises_integrity()
        assert user2.id is None

    async def test_create_user_failure_dup_username(self):
        username = faker.first_name()
        user1 = UserModel(**self._make_data(username=username))
        user2 = UserModel(**self._make_data(username=username))

        self.db.add(user1)
        await self.db.commit()

        self.db.add(user2)
        await self._assert_commit_raises_integrity()
        assert user2.id is None

    @pytest.mark.parametrize(
        "field", ["name", "username", "email", "hashed_password"]
    )
    async def test_create_user_failure_null_fields(self, field):
        data = self._make_data(**{field: None})
        user = UserModel(**data)

        self.db.add(user)
        await self._assert_commit_raises_integrity()
        assert user.id is None

    @pytest.mark.parametrize(
        "field,max_length",
        [
            ("name", 256),
            ("username", 64),
            ("email", 256),
        ],
    )
    async def test_create_user_failure_exceed_max_length(
        self, field, max_length
    ):
        data = self._make_data(**{field: "A" * (max_length + 1)})
        user = UserModel(**data)

        self.db.add(user)
        with pytest.raises(StatementError):
            await self.db.commit()
        assert user.id is None

    async def test_create_user_default_is_master_false(self):
        data = self._make_data()
        data.pop("is_master", None)
        user = UserModel(**data)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        assert user.is_master is False
