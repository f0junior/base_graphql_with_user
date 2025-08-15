from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import UserModel


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).filter_by(id=user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).filter_by(email=email)
        )
        return result.scalar_one_or_none()

    async def add(self, user: UserModel) -> None:
        self.session.add(user)

    async def delete(self, user: UserModel) -> None:
        await self.session.delete(user)

    async def refresh(self, user: UserModel) -> None:
        await self.session.refresh(user)
