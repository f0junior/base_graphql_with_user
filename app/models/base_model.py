from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def __repr__(self) -> str:
        attrs = vars(self)
        cls_name = self.__class__.__name__
        filtered = {
            k: v
            for k, v in attrs.items()
            if not k.startswith("_") and k != "hashed_password"
        }

        parts = [f"{k}={v!r}" for k, v in filtered.items()]
        return f"<{cls_name}({', '.join(parts)})>"
