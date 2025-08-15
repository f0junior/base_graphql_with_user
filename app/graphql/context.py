from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from fastapi import Request, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext

from app.exceptions import (
    ExpiredSessionError,
    PermissionDeniedError,
    UserNotFoundError,
)
from app.models.user_model import UserModel
from app.services.session_service import SessionService
from app.services.user_auth_service import UserAuthService
from app.services.user_service import UserService
from app.utils.validators import is_uuid4


@dataclass
class Context(BaseContext):
    session: AsyncSession
    redis: Redis
    request: Request
    response: Response
    user: Optional[UserModel] = None

    _user_service: Optional[UserService] = field(init=False, default=None)
    _user_auth_service: Optional[UserAuthService] = field(
        init=False, default=None
    )
    _session_service: Optional[SessionService] = field(
        init=False, default=None
    )

    @property
    def user_service(self) -> UserService:
        if self._user_service is None:
            self._user_service = UserService(self.session)
        return self._user_service

    @property
    def user_auth_service(self) -> UserAuthService:
        if self._user_auth_service is None:
            self._user_auth_service = UserAuthService(self.session)
        return self._user_auth_service

    @property
    def session_service(self) -> SessionService:
        if self._session_service is None:
            self._session_service = SessionService(self.redis)
        return self._session_service

    def set_cookie(self, session_id: UUID) -> None:
        self.response.set_cookie(
            key="session",
            value=str(session_id),
            httponly=True,
            secure=True,
            max_age=self.session_service.TIME_TO_SESSION - 30,
            samesite="strict",
            path="/",
        )

    async def authenticate_user(self) -> bool:
        session_id = self.request.cookies.get("session")
        if not session_id:
            raise PermissionDeniedError

        if not is_uuid4(session_id):
            raise ExpiredSessionError()

        user = await self.session_service.get_user_id_from_session(
            UUID(session_id)
        )
        if not user:
            raise ExpiredSessionError

        user = await self.session.get(UserModel, ident=user.id)
        if not user:
            raise UserNotFoundError

        self.user = user

        return True
