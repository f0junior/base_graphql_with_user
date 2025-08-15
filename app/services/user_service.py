from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.models.user_model import UserModel
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import (
    UserCreate,
    UserDelete,
    UserRead,
    UserUpdate,
)
from app.utils import security


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)

    @asynccontextmanager
    async def _transaction(self, *, email=None, username=None):
        try:
            yield
            await self.session.commit()
        except IntegrityError as exc_info:
            await self.session.rollback()

            error_str = str(exc_info.orig)
            if email and "ix_users_email" in error_str:
                raise DuplicateEmailError(str(email))
            if username and "ix_users_username" in error_str:
                raise DuplicateUsernameError(str(username))

            raise
        except Exception:
            await self.session.rollback()
            raise

    async def create_user(self, data: UserCreate) -> UserRead:
        async with self._transaction(email=data.email, username=data.username):
            user = UserModel(
                name=data.name,
                username=data.username,
                email=data.email,
                hashed_password=security.hash_password(data.password),
            )
            await self.repository.add(user)
            await self.session.flush()
            await self.repository.refresh(user)
            return UserRead.model_validate(user)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserRead:
        async with self._transaction(email=data.email, username=data.username):
            user = await self.repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError()

            if not security.verify_password(data.password, user.hashed_password):
                raise InvalidCredentialsError()

            for field, value in data.model_dump(
                exclude_unset=True, exclude_none=True
            ).items():
                if field != "password":
                    setattr(user, field, value)

            await self.session.flush()
            await self.repository.refresh(user)
            return UserRead.model_validate(user)

    async def get_user_by_id(self, user_id: UUID) -> UserRead:
        async with self._transaction():
            user = await self.repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError()

            return UserRead.model_validate(user)

    async def delete_user(self, user_id: UUID, data: UserDelete) -> None:
        async with self._transaction():
            user = await self.repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError()

            if not security.verify_password(data.password, user.hashed_password):
                raise InvalidCredentialsError()

            await self.repository.delete(user)
            await self.session.flush()
