from typing import Any, Dict, Optional

from graphql import GraphQLError


class AppError(GraphQLError):
    """Exceção base da aplicação."""

    def __init__(
        self, message: str, extensions: Optional[Dict[str, Any]] = None
    ):
        if extensions is None:
            extensions = {}
        extensions.setdefault("code", self.__class__.__name__)
        super().__init__(message=message, extensions=extensions)


class NotFoundError(AppError):
    """Recurso não encontrado."""

    def __init__(self, message: str = "Recurso não encontrado"):
        super().__init__(message)


class ConflictError(AppError):
    """Erro de conflito, como violação de unicidade."""

    def __init__(self, message: str = "Conflito de dados."):
        super().__init__(message)


class UnauthorizedError(AppError):
    """Erro de autenticação."""

    def __init__(self, message: str = "Não autorizado."):
        super().__init__(message)


class ForbiddenError(AppError):
    """Erro de autorização."""

    def __init__(self, message: str = "Acesso proibido."):
        super().__init__(message)


class UserNotFoundError(NotFoundError):
    def __init__(self):
        msg = (
            "Você lançou 'Localizar Criatura', mas… não houve sucesso."
            + "Esse usuário não existe."
        )

        super().__init__(msg)


class DuplicateEmailError(ConflictError):
    def __init__(self, email: str):
        msg = (
            "Não aceitamos doppelganger, "
            + f"usuário já cadastrado com o email: {email}."
        )

        super().__init__(msg)


class DuplicateUsernameError(ConflictError):
    def __init__(self, username: str):
        msg = (
            "Não aceitamos doppelganger, "
            + f"usuário já cadastrado com o nickname: {username}."
        )

        super().__init__(msg)


class InvalidCredentialsError(UnauthorizedError):
    def __init__(self):
        msg = (
            "Senha inválida. Um gnomo aleatório explode no fundo. "
            + "Coincidência? Provavelmente."
        )

        super().__init__(msg)


class PermissionDeniedError(UnauthorizedError):
    def __init__(self):
        msg = (
            "OH OH OH, já viu mago lançar magia sem preparar. Vai lá fazer login"
            + " e aí depois tentar fazer o que pretendia."
        )

        super().__init__(msg)


class ExpiredSessionError(UnauthorizedError):
    def __init__(self):
        msg = (
            "Sua aventura demorou demais e o pergaminho (sessão) venceu. "
            + "Faça login novamente."
        )

        super().__init__(msg)
