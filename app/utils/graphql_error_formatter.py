from dataclasses import dataclass
from typing import Any, Dict, List

from graphql import GraphQLError

from app.utils.error_code import ErrorCode


@dataclass
class ErrorHandler:
    pattern: str
    code: str
    friendly_msg: str


class GraphQLErrorFormatter:
    def __init__(self):
        self.handlers: List[ErrorHandler] = [
            self._invalid_query_field(),
            self._invalid_type_input(),
            self._invalid_value_input(),
            self._missing_required_input(),
            self._unexpected_input(),
        ]

    def format(self, error: GraphQLError) -> Dict[str, Any]:
        message = getattr(error, "original_error", None)
        if message is None:
            message = error.formatted.get("message", "")

        message = f"{message}"

        for handler in self.handlers:
            if handler.pattern in message:
                return self._build_error_dict(
                    message=message,
                    code=handler.code,
                    friendly_msg=handler.friendly_msg,
                )

        return self._formatted_error(error)

    def format_all(self, errors: List[GraphQLError]) -> List[object] | None:
        return [self.format(error) for error in errors]

    def _build_error_dict(
        self, message: str, code: str, friendly_msg: str
    ) -> Dict[str, Any]:
        return {
            "message": friendly_msg,
            "code": code,
            "details": message,
        }

    def _formatted_error(self, error: GraphQLError) -> Dict[str, Any]:
        formatted_error = error.formatted
        extensions = formatted_error.get("extensions", {})

        message = formatted_error.get("message", "Unknown error.")
        code = extensions.get("code", ErrorCode.UNKNOWN_ERROR)

        return {"message": message, "code": code, "details": message}

    def _invalid_query_field(self) -> ErrorHandler:
        return ErrorHandler(
            pattern="Cannot query field",
            code=ErrorCode.INVALID_QUERY_FIELD,
            friendly_msg=(
                "Você tentou abrir uma porta… mas ela era só um desenho na parede."
            ),
        )

    def _invalid_type_input(self) -> ErrorHandler:
        return ErrorHandler(
            pattern="cannot represent a",
            code=ErrorCode.INVALID_ARGUMENT_TYPE,
            friendly_msg=(
                "Sua tentativa ativou alertas, uma runa de segurança, "
                "e provocou gargalhadas em todo o conselho arcano do sistema. "
                "Dá uma revisada aí, nobre conjurador."
            ),
        )

    def _invalid_value_input(self) -> ErrorHandler:
        return ErrorHandler(
            pattern="validation error",
            code=ErrorCode.INVALID_ARGUMENT_VALUE,
            friendly_msg=(
                "Sua tentativa ativou alertas, uma runa de segurança, "
                "e provocou gargalhadas em todo o conselho arcano do sistema. "
                "Dá uma revisada aí, nobre conjurador."
            ),
        )

    def _missing_required_input(self) -> ErrorHandler:
        return ErrorHandler(
            pattern="required type",
            code=ErrorCode.MISSING_REQUIRED_INPUT,
            friendly_msg=(
                "Seu feitiço falhou! Está faltando pelo menos um componente essencial. "
                "Verifique seu grimório e tente novamente."
            ),
        )

    def _unexpected_input(self) -> ErrorHandler:
        return ErrorHandler(
            pattern="not defined",
            code=ErrorCode.UNEXPECTED_INPUT,
            friendly_msg=(
                "Já falamos que Crina de Leopardo não é o componente dessa magia. "
                "Retire o componente, e fingimos que nada aconteceu."
            ),
        )
