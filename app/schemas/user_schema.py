from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator, model_validator

from app.utils.validators import validate_password_strength

from .base_schema import AppBaseModel


class PasswordValidatedModel(AppBaseModel):
    password: str = Field(..., min_length=8)

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, password: str) -> str:
        return validate_password_strength(password)


class UserCreate(PasswordValidatedModel):
    name: str = Field(..., min_length=5, max_length=256)
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr = Field(..., max_length=256)


class UserUpdate(PasswordValidatedModel):
    name: Optional[str] = Field(None, min_length=5, max_length=256)
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    email: Optional[EmailStr] = Field(None, max_length=256)

    @model_validator(mode="after")
    def check_at_least_one_field(cls, values):
        if not (values.name or values.username or values.email):
            msg = (
                "Nenhum campo foi atualizado, ao "
                + "menos um campo deve ser informado para atualizar."
            )
            raise ValueError(msg)
        return values


class UserChangePassword(AppBaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password", mode="after")
    @classmethod
    def validate_password(cls, password: str) -> str:
        return validate_password_strength(password)

    @model_validator(mode="after")
    def check_passwords_equals(cls, values):
        if values.current_password == values.new_password:
            raise ValueError("A senha nova não pode ser igual a atual.")
        return values


class UserLogin(PasswordValidatedModel):
    email: EmailStr


class UserDelete(AppBaseModel):
    password: str = Field(..., min_length=8)


class UserRead(AppBaseModel):
    id: UUID
    name: str
    username: str
    email: EmailStr
    is_master: bool
