from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, IDMixin, TimestampMixin


class UserModel(Base, IDMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    username: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, unique=True
    )
    email: Mapped[str] = mapped_column(
        String(256), nullable=False, index=True, unique=True
    )
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    is_master: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
