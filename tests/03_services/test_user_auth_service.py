from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from faker import Faker

from app.exceptions import InvalidCredentialsError, UserNotFoundError
from app.models.user_model import UserModel
from app.schemas.user_schema import UserChangePassword, UserLogin, UserRead
from app.services.user_auth_service import UserAuthService
from app.utils import security

faker = Faker()


@pytest.mark.anyio
class TestUserAuthService:
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
        svc = UserAuthService(session_mock)
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

    async def test_login_user_success(
        self, repository_mock, service: UserAuthService
    ):
        data = self.make_data()
        user_model = self.mock_user_model(**data)
        user_login = UserLogin(email=data["email"], password=data["password"])

        repository_mock.get_by_email = AsyncMock()
        repository_mock.get_by_email.return_value = user_model

        service.session.commit = AsyncMock()

        with patch.object(
            security, "verify_password", return_value=True
        ) as mock_verify:
            result = await service.login_user(user_login)

        mock_verify.assert_called_once_with(
            user_login.password, user_model.hashed_password
        )

        assert isinstance(result, UserRead)
        expected = UserRead.model_validate(user_model)
        assert result.model_dump() == expected.model_dump()

        repository_mock.get_by_email.assert_awaited_once_with(user_login.email)
        service.session.commit.assert_awaited_once()

    async def test_login_user_failure_nonexistent_user(
        self, repository_mock, service: UserAuthService
    ):
        user_login = UserLogin(
            email=faker.email(), password=self.strong_password()
        )

        service.session.rollback = AsyncMock()

        repository_mock.get_by_email = AsyncMock()
        repository_mock.get_by_email.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.login_user(user_login)

        repository_mock.get_by_email.assert_awaited_once_with(user_login.email)
        service.session.rollback.assert_awaited_once()

    async def test_login_user_failure_invalid_password(
        self, repository_mock, service: UserAuthService
    ):
        data = self.make_data()
        user_model = self.mock_user_model(**data)
        user_login = UserLogin(email=data["email"], password=data["password"])

        service.session.rollback = AsyncMock()

        repository_mock.get_by_email = AsyncMock()
        repository_mock.get_by_email.return_value = user_model

        with patch.object(
            security, "verify_password", return_value=False
        ) as mock_verify:
            with pytest.raises(InvalidCredentialsError):
                await service.login_user(user_login)

        mock_verify.assert_called_once_with(
            user_login.password, user_model.hashed_password
        )

        repository_mock.get_by_email.assert_awaited_once_with(user_login.email)
        service.session.rollback.assert_awaited_once()

    async def test_login_user_failure_propagate_generic_error(
        self, repository_mock, service: UserAuthService
    ):
        user_login = UserLogin(
            email=faker.email(), password=self.strong_password()
        )

        service.session.rollback = AsyncMock()
        service.session.commit = AsyncMock()
        service.session.flush = AsyncMock()
        repository_mock.get_by_email = AsyncMock()

        repository_mock.get_by_email.side_effect = Exception(
            "unexpected error"
        )

        with pytest.raises(Exception, match="unexpected error"):
            await service.login_user(user_login)

        repository_mock.get_by_email.assert_awaited_once_with(user_login.email)
        service.session.rollback.assert_awaited_once()
        service.session.commit.assert_not_awaited()
        service.session.flush.assert_not_awaited()

    async def test_change_password_success(
        self, repository_mock, service: UserAuthService
    ):
        user_model = self.mock_user_model(**self.make_data())
        user_change_pass = UserChangePassword(
            current_password=self.strong_password(),
            new_password=self.strong_password(),
        )

        old_hashed = user_model.hashed_password

        repository_mock.get_by_id = AsyncMock()
        repository_mock.get_by_id.return_value = user_model

        service.session.flush = AsyncMock()
        service.session.commit = AsyncMock()
        repository_mock.refresh = AsyncMock()

        with patch.object(
            security, "verify_password", return_value=True
        ) as mock_verify:
            with patch.object(
                security, "hash_password", return_value="new_hashed"
            ) as mock_hash:
                result = await service.change_password(
                    user_model.id, user_change_pass
                )

        assert isinstance(result, UserRead)
        assert user_model.hashed_password != old_hashed
        expected = UserRead.model_validate(user_model)
        assert result.model_dump() == expected.model_dump()

        mock_verify.assert_called_once_with(
            user_change_pass.current_password, old_hashed
        )
        mock_hash.assert_called_once_with(user_change_pass.new_password)

        repository_mock.get_by_id.assert_awaited_once_with(user_model.id)
        service.session.flush.assert_awaited_once()
        service.session.commit.assert_awaited_once()
        repository_mock.refresh.assert_awaited_once_with(user_model)

    async def test_change_password_failure_nonexistent_user(
        self, repository_mock, service: UserAuthService
    ):
        user_id = faker.uuid4(cast_to=None)
        user_change_pass = UserChangePassword(
            current_password=self.strong_password(),
            new_password=self.strong_password(),
        )

        repository_mock.get_by_id = AsyncMock()
        repository_mock.get_by_id.return_value = None

        service.session.commit = AsyncMock()
        service.session.rollback = AsyncMock()

        with pytest.raises(UserNotFoundError):
            await service.change_password(user_id, user_change_pass)

        repository_mock.get_by_id.assert_awaited_once_with(user_id)
        service.session.commit.assert_not_awaited()
        service.session.rollback.assert_awaited_once()

    async def test_change_password_failure_invalid_password(
        self, repository_mock, service: UserAuthService
    ):
        user_model = self.mock_user_model(**self.make_data())
        user_change_pass = UserChangePassword(
            current_password=self.strong_password(),
            new_password=self.strong_password(),
        )

        repository_mock.get_by_id = AsyncMock()
        repository_mock.get_by_id.return_value = user_model

        service.session.commit = AsyncMock()
        service.session.rollback = AsyncMock()

        with patch.object(
            security, "verify_password", return_value=False
        ) as verify_mock:
            with pytest.raises(InvalidCredentialsError):
                await service.change_password(user_model.id, user_change_pass)

        verify_mock.assert_called_once_with(
            user_change_pass.current_password, user_model.hashed_password
        )

        repository_mock.get_by_id.assert_awaited_once_with(user_model.id)
        service.session.commit.assert_not_awaited()
        service.session.rollback.assert_awaited_once()

    async def test_change_password_failure_propagate_generic_error(
        self, repository_mock, service: UserAuthService
    ):
        user_id = faker.uuid4(cast_to=None)
        user_change_pass = UserChangePassword(
            current_password=self.strong_password(),
            new_password=self.strong_password(),
        )

        repository_mock.get_by_id = AsyncMock()
        repository_mock.get_by_id.side_effect = Exception("unexpected error")

        service.session.rollback = AsyncMock()
        service.session.commit = AsyncMock()
        service.session.flush = AsyncMock()

        with pytest.raises(Exception, match="unexpected error"):
            await service.change_password(user_id, user_change_pass)

        repository_mock.get_by_id.assert_awaited_once_with(user_id)
        service.session.flush.assert_not_awaited()
        service.session.commit.assert_not_awaited()
        service.session.rollback.assert_awaited_once()
