import strawberry
from graphql import GraphQLError
from strawberry.types import Info

import app.graphql.types.user_types as user_types
from app.graphql.context import Context
from app.graphql.permission import IsAuthenticated
from app.graphql.types.user_types import UserType


@strawberry.type
class UserMutation:
    @strawberry.mutation
    async def create_user(
        self, info: Info[Context, None], data: user_types.UserCreateInput
    ) -> UserType:
        try:
            user = await info.context.user_service.create_user(
                data.to_pydantic()
            )
            return UserType.from_pydantic(user)
        except GraphQLError:
            raise
        except Exception as e:
            raise GraphQLError(f"Erro inesperado ao criar usuário: {str(e)}")

    @strawberry.mutation
    async def login(
        self, info: Info[Context, None], data: user_types.UserLoginInput
    ) -> UserType:
        try:
            context = info.context
            user = await context.user_auth_service.login_user(
                data.to_pydantic()
            )

            session_id = await context.session_service.create_session(user)
            context.set_cookie(session_id)

            return UserType.from_pydantic(user)
        except GraphQLError:
            raise
        except Exception as e:
            raise GraphQLError(f"Erro inesperado ao fazer login: {str(e)}")

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_user(
        self,
        info: Info[Context, None],
        data: user_types.UserUpdateInput,
    ) -> UserType:
        try:
            user = info.context.user
            if not user:
                raise GraphQLError("Usuário não autenticado ou inválido.")

            userRead = await info.context.user_service.update_user(
                user.id, data.to_pydantic()
            )
            return UserType.from_pydantic(userRead)
        except GraphQLError:
            raise
        except Exception as e:
            raise GraphQLError(
                f"Erro inesperado na atualização do usuário: {str(e)}"
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def change_password(
        self,
        info: Info[Context, None],
        data: user_types.UserChangePasswordInput,
    ) -> UserType:
        try:
            user = info.context.user
            if not user:
                raise GraphQLError("Usuário não autenticado ou inválido.")

            userRead = await info.context.user_auth_service.change_password(
                user.id, data.to_pydantic()
            )
            return UserType.from_pydantic(userRead)
        except GraphQLError:
            raise
        except Exception as e:
            raise GraphQLError(
                f"Erro inesperado na atualização do usuário: {str(e)}"
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_user(
        self, info: Info[Context, None], data: user_types.UserDeleteInput
    ) -> bool:
        try:
            user = info.context.user
            if not user:
                raise GraphQLError("Usuário não autenticado ou inválido.")

            await info.context.user_service.delete_user(
                user.id, data.to_pydantic()
            )
            return True
        except GraphQLError:
            raise
        except Exception as e:
            raise GraphQLError(f"Erro inesperado ao deletar usuário: {str(e)}")
