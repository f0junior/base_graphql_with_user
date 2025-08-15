from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from faker import Faker
from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.models.user_model import UserModel
from app.schemas.user_schema import (
    UserCreate,
    UserDelete,
    UserRead,
    UserUpdate,
)
from app.services.user_service import UserService
from app.utils import security

faker = Faker()


@pytest.mark.anyio
class TestUserService:
    @pytest.fixture
    def session_mock(self):
        session = AsyncMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def repository_mock(self, session_mock):
        repository = MagicMock()
        repository.add = AsyncMock(return_value=None)
        repository.refresh = AsyncMock()
        repository.get_by_id = AsyncMock()
        repository.delete = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, session_mock, repository_mock):
        svc = UserService(session_mock)
        svc.repository = repository_mock
        return svc

    def strong_password(self) -> str:
        return faker.password(
            length=8,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True,
        )

    def make_data(self, **kwargs: Any) -> Dict[str, Any]:
        data = {
            "name": faker.name(),
            "username": faker.first_name(),
            "email": faker.email(),
            "password": self.strong_password(),
        }
        data.update(**kwargs)

        return data

    def mock_user_model(self, **kwargs: Any) -> UserModel:
        return UserModel(
            id=kwargs.get("id", faker.uuid4(cast_to=None)),
            name=kwargs.get("name", faker.name()),
            username=kwargs.get("username", faker.first_name()),
            email=kwargs.get("email", faker.email()),
            hashed_password=kwargs.get("hashed_password", "fake_hashed"),
            is_master=kwargs.get("is_master", False),
        )

    async def test_create_user_success(
        self, repository_mock, service: UserService
    ):
        user_create = UserCreate(**self.make_data())
        user_model = self.mock_user_model(**user_create.model_dump())

        async def refresh_side_effect(user):
            user.id = user_model.id
            user.is_master = user_model.is_master

        repository_mock.refresh.side_effect = refresh_side_effect

        with patch.object(
            security, "hash_password", return_value=user_model.hashed_password
        ) as mock_verify:
            result = await service.create_user(user_create)

        mock_verify.assert_called_once_with(user_create.password)

        assert isinstance(result, UserRead)
        expected = UserRead.model_validate(user_model)
        assert result.model_dump() == expected.model_dump()
        repository_mock.add.assert_awaited_once()

    @pytest.mark.parametrize(
        "override",
        [
            {"orig": "ix_users_email", "error_class": DuplicateEmailError},
            {
                "orig": "ix_users_username",
                "error_class": DuplicateUsernameError,
            },
        ],
    )
    async def test_create_user_failure_duplicated_value_field(
        self, override, repository_mock, service: UserService
    ):
        user_create = UserCreate(**self.make_data())

        repository_mock.add.side_effect = IntegrityError(
            statement="INSERT INTO users ...",
            params={},
            orig=Exception(
                f'duplicate key value violates unique constraint "{override["orig"]}"'
            ),
        )

        service.session.rollback = AsyncMock()

        with pytest.raises(override["error_class"]) as exc_info:
            await service.create_user(user_create)

        service.session.rollback.assert_awaited_once()

        assert {
            "ix_users_email": user_create.email,
            "ix_users_username": user_create.username,
        }[override["orig"]] in str(exc_info.value)

    async def test_update_user_success_all_fields(
        self, repository_mock, service: UserService
    ):
        user_model = self.mock_user_model(**self.make_data())
        user_update = UserUpdate(
            name="Ash Ketchum",
            username="Red",
            email="example@example.com",
            password="Senh@123",
        )

        repository_mock.get_by_id.return_value = user_model

        async def refresh_side_effect(user):
            user.name = user_update.name
            user.username = user_update.username
            user.email = user_update.email

        repository_mock.refresh.side_effect = refresh_side_effect

        with patch.object(
            security, "verify_password", return_value=True
        ) as mock_verify:
            result = await service.update_user(user_model.id, user_update)

        mock_verify.assert_called_once_with(
            user_update.password, user_model.hashed_password
        )

        assert isinstance(result, UserRead)
        assert result.name == user_update.name
        assert result.username == user_update.username
        assert result.email == user_update.email
        assert result.is_master == user_model.is_master
        repository_mock.refresh.assert_awaited_once()

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"name": "Ash Ketchum"},
            {"username": "Red"},
            {"email": "example@example.com"},
        ],
    )
    async def test_update_user_success_one_field(
        self, kwargs, repository_mock, service: UserService
    ):
        user_model = self.mock_user_model(**self.make_data())
        user_update = UserUpdate(password="Senh@123", **kwargs)

        repository_mock.get_by_id.return_value = user_model

        async def refresh_side_effect(user):
            for key, value in user_update.model_dump(
                exclude_unset=True
            ).items():
                setattr(user, key, value)

        repository_mock.refresh.side_effect = refresh_side_effect

        with patch.object(
            security, "verify_password", return_value=True
        ) as mock_verify:
            result = await service.update_user(user_model.id, user_update)

        mock_verify.assert_called_once_with(
            user_update.password, user_model.hashed_password
        )

        assert isinstance(result, UserRead)

        result_data = result.model_dump()
        original_data = UserRead.model_validate(user_model).model_dump()

        for key, original_value in original_data.items():
            if key in kwargs:
                assert result_data[key] == kwargs[key]
            else:
                assert result_data[key] == original_value

        repository_mock.refresh.assert_awaited_once()

    async def test_update_user_failure_nonexistent_user(
        self, repository_mock, service: UserService
    ):
        user_id = faker.uuid4(cast_to=None)
        data = UserUpdate(**{"password": "Senh@123", "username": "Red"})
        repository_mock.get_by_id.return_value = None

        service.session.rollback = AsyncMock()

        with pytest.raises(UserNotFoundError):
            await service.update_user(user_id, data)

        repository_mock.get_by_id.assert_awaited_once_with(user_id)
        service.session.rollback.assert_awaited_once()

    async def test_update_user_failure_invalid_password(
        self, repository_mock, service: UserService
    ):
        user_model = self.mock_user_model(**self.make_data())
        user_update = UserUpdate(**{"username": "Red", "password": "Senh@123"})

        repository_mock.get_by_id.return_value = user_model

        service.session.rollback = AsyncMock()

        with patch.object(
            security, "verify_password", return_value=False
        ) as mock_verify:
            with pytest.raises(InvalidCredentialsError):
                await service.update_user(user_model.id, user_update)

        mock_verify.assert_called_once_with(
            user_update.password, user_model.hashed_password
        )

        repository_mock.get_by_id.assert_awaited_once_with(user_model.id)
        service.session.rollback.assert_awaited_once()

    @pytest.mark.parametrize(
        "override",
        [
            {"orig": "ix_users_email", "error_class": DuplicateEmailError},
            {
                "orig": "ix_users_username",
                "error_class": DuplicateUsernameError,
            },
        ],
    )
    async def test_update_user_failure_duplicated_value_field(
        self, override, repository_mock, service: UserService
    ):
        user_model = self.mock_user_model(**self.make_data())
        user_update = UserUpdate(
            **{
                "username": "Red",
                "email": "example@example.com",
                "password": "Senh@123",
            }
        )

        repository_mock.get_by_id.return_value = user_model

        service.session.flush = AsyncMock()
        service.session.flush.side_effect = IntegrityError(
            statement="UPDATE users ...",
            params={},
            orig=Exception(
                f'duplicate key value violates unique constraint "{override["orig"]}"'
            ),
        )

        service.session.rollback = AsyncMock()

        with patch.object(
            security, "verify_password", return_value=True
        ) as mock_verify:
            with pytest.raises(override["error_class"]) as exc_info:
                await service.update_user(user_model.id, user_update)

        mock_verify.assert_called_once_with(
            user_update.password, user_model.hashed_password
        )

        service.session.flush.assert_awaited_once()
        service.session.rollback.assert_awaited_once()

        assert {
            "ix_users_email": getattr(user_update, "email", ""),
            "ix_users_username": getattr(user_update, "username", ""),
        }[override["orig"]] in str(exc_info.value)

    async def test_get_user_by_id_success(
        self, repository_mock, service: UserService
    ):
        user_model = self.mock_user_model(**self.make_data())

        repository_mock.get_by_id.return_value = user_model

        service.session.commit = AsyncMock()

        result = await service.get_user_by_id(user_model.id)

        assert isinstance(result, UserRead)
        expected = UserRead.model_validate(user_model)
        assert result.model_dump() == expected.model_dump()

        repository_mock.get_by_id.assert_awaited_once_with(user_model.id)
        service.session.commit.assert_awaited_once()

    async def test_get_user_by_id_failure_nonexistent_user(
        self, repository_mock, service: UserService
    ):
        user_id = faker.uuid4(cast_to=None)

        repository_mock.get_by_id.return_value = None

        service.session.rollback = AsyncMock()

        with pytest.raises(UserNotFoundError):
            await service.get_user_by_id(user_id)

        repository_mock.get_by_id.assert_awaited_once_with(user_id)
        service.session.rollback.assert_awaited_once()

    async def test_delete_user_success(
        self, repository_mock, service: UserService
    ):
        user_model = self.mock_user_model(**self.make_data())
        user_delete = UserDelete(password="Senh@123")

        repository_mock.get_by_id.return_value = user_model

        repository_mock.delete = AsyncMock()
        service.session.flush = AsyncMock()

        with patch.object(
            security, "verify_password", return_value=True
        ) as moock_verify:
            await service.delete_user(user_model.id, user_delete)

        moock_verify.assert_called_once_with(
            user_delete.password, user_model.hashed_password
        )

        repository_mock.delete.assert_awaited_once_with(user_model)
        service.session.flush.assert_awaited_once()

    async def test_delete_user_failure_nonexistent_user(
        self, repository_mock, service: UserService
    ):
        user_id = faker.uuid4(cast_to=None)
        user_delete = UserDelete(password="Senh@123")

        repository_mock.get_by_id.return_value = None

        service.session.rollback = AsyncMock()

        with pytest.raises(UserNotFoundError):
            await service.delete_user(user_id, user_delete)

        repository_mock.get_by_id.assert_awaited_once_with(user_id)
        service.session.rollback.assert_awaited_once()

    async def test_delete_user_failure_invalid_password(
        self, repository_mock, service: UserService
    ):
        user_model = self.mock_user_model(**self.make_data())
        user_delete = UserDelete(password="Senh@123")

        repository_mock.get_by_id.return_value = user_model

        service.session.rollback = AsyncMock()

        with patch.object(
            security, "verify_password", return_value=False
        ) as mock_verify:
            with pytest.raises(InvalidCredentialsError):
                await service.delete_user(user_model.id, user_delete)

        mock_verify.assert_called_once_with(
            user_delete.password, user_model.hashed_password
        )

        repository_mock.get_by_id.assert_awaited_once_with(user_model.id)
        service.session.rollback.assert_awaited_once()

    @pytest.mark.parametrize(
        "method_name,args",
        [
            (
                "create_user",
                [
                    UserCreate(
                        **{
                            "name": faker.name(),
                            "username": faker.first_name(),
                            "email": "test@example.com",
                            "password": "Senha@123",
                        }
                    )
                ],
            ),
            (
                "update_user",
                [
                    faker.uuid4(cast_to=None),
                    UserUpdate(
                        **{"username": "NewName", "password": "Senha@123"}
                    ),
                ],
            ),
            ("get_user_by_id", [faker.uuid4(cast_to=None)]),
            (
                "delete_user",
                [faker.uuid4(cast_to=None), UserDelete(password="Senha@123")],
            ),
        ],
    )
    async def test_service_methods_propagate_generic_error(
        self, method_name, args, repository_mock, service: UserService
    ):
        service.session.rollback = AsyncMock()
        service.session.commit = AsyncMock()
        service.session.flush = AsyncMock()

        def side_effect(*a, **k):
            raise Exception("unexpected error")

        repository_mock.get_by_id.side_effect = side_effect
        repository_mock.add.side_effect = side_effect
        repository_mock.delete.side_effect = side_effect
        service.session.flush.side_effect = side_effect

        method = getattr(service, method_name)

        with pytest.raises(Exception, match="unexpected error"):
            await method(*args)

        service.session.rollback.assert_awaited_once()
        service.session.commit.assert_not_awaited()
