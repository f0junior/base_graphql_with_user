import strawberry
from strawberry.experimental import pydantic

import app.schemas.user_schema as user


@pydantic.input(model=user.UserCreate, all_fields=True)
class UserCreateInput:
    pass


@pydantic.input(model=user.UserLogin, all_fields=True)
class UserLoginInput:
    pass


@pydantic.input(model=user.UserUpdate, all_fields=True)
class UserUpdateInput:
    pass


@pydantic.input(model=user.UserChangePassword, all_fields=True)
class UserChangePasswordInput:
    pass


@pydantic.input(model=user.UserDelete, all_fields=True)
class UserDeleteInput:
    pass


@strawberry.type
class UserLogoutType:
    success: bool


@pydantic.type(model=user.UserRead, all_fields=True, include_computed=True)
class UserType:
    pass
