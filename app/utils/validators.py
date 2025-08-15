import re
from typing import Any
from uuid import UUID


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("A senha deve ter no mínimo 8 caracteres")

    if not re.search(r"[A-Z]", password):
        raise ValueError("A senha deve conter pelo menos uma letra maiúscula")

    if not re.search(r"\d", password):
        raise ValueError("A senha deve conter pelo menos um número")

    if not re.search(r"[^a-zA-Z0-9\s]", password):
        raise ValueError(
            "A senha deve conter pelo menos um caractere especial"
        )

    return password


def is_uuid4(value: Any) -> bool:
    try:
        val = UUID(value, version=4)
    except (ValueError, AttributeError, TypeError):
        return False
    return val.version == 4
