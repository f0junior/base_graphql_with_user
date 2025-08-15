from uuid import UUID

import strawberry
from graphql import GraphQLError
from strawberry.types import Info

from app.exceptions import UserNotFoundError
from app.graphql.context import Context
from app.graphql.permission import IsAuthenticated
from app.graphql.types.user_types import (
    UserLogoutType,
    UserType,
)


@strawberry.type
class UserQuery:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def me(self, info: Info[Context, None]) -> UserType:
        try:
            user = info.context.user
            if not user:
                raise UserNotFoundError

            user = await info.context.user_service.get_user_by_id(user.id)
            return UserType.from_pydantic(user)
        except GraphQLError:
            raise
        except Exception as e:
            raise GraphQLError(f"Erro inesperado ao buscar usuário: {str(e)}")

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def logout(self, info: Info[Context, None]) -> UserLogoutType:
        try:
            session_id = UUID(info.context.request.cookies.get("session"))
            if session_id:
                await info.context.session_service.delete_session(session_id)
                info.context.response.delete_cookie("session")

            return UserLogoutType(success=True)
        except GraphQLError:
            raise
        except Exception as e:
            raise GraphQLError(f"Erro inesperado ao realizar logout: {str(e)}")
