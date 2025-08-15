from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import (
    UserChangePassword,
    UserLogin,
    UserRead,
)
from app.utils import security


class UserAuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)

    @asynccontextmanager
    async def _transaction(self):
        try:
            yield
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def login_user(self, data: UserLogin) -> UserRead:
        async with self._transaction():
            user = await self.repository.get_by_email(data.email)
            if not user:
                raise UserNotFoundError()

            if not security.verify_password(
                data.password, user.hashed_password
            ):
                raise InvalidCredentialsError()

            return UserRead.model_validate(user)

    async def change_password(
        self, user_id: UUID, data: UserChangePassword
    ) -> UserRead:
        async with self._transaction():
            user = await self.repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError()

            if not security.verify_password(
                data.current_password, user.hashed_password
            ):
                raise InvalidCredentialsError()

            user.hashed_password = security.hash_password(data.new_password)
            await self.session.flush()
            await self.repository.refresh(user)
            return UserRead.model_validate(user)
