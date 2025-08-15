from enum import Enum


class ErrorCode(str, Enum):
    INVALID_ARGUMENT_TYPE = "InvalidArgumentTypeError"
    INVALID_ARGUMENT_VALUE = "InvalidArgumentValueError"
    INVALID_QUERY_FIELD = "InvalidQueryFieldError"
    MISSING_REQUIRED_INPUT = "MissingRequiredInputError"
    UNEXPECTED_INPUT = "UnexpectedInputError"
    UNKNOWN_ERROR = "UnknownError"
