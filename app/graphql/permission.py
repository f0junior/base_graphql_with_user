import typing

import strawberry
from graphql import GraphQLError
from strawberry.permission import BasePermission


class IsAuthenticated(BasePermission):
    def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs
    ) -> bool:
        try:
            return info.context.authenticate_user()
        except GraphQLError as e:
            self.error_class = type(e)
            return False
        except Exception as e:
            self.message = str(e)
            self.error_extensions = {"code": type(e)}
            return False

    def on_unauthorized(self) -> None:
        raise self.error_class()  # type: ignore
