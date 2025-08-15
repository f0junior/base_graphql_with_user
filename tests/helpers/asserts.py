from typing import Any, Optional, Type

import pytest
from pydantic import BaseModel, ValidationError


def assert_schema_equals_data(
    schema_cls: Type[BaseModel], data: dict[str, Any]
) -> None:
    schema = schema_cls(**data)
    for key, value in data.items():
        schema_value = getattr(schema, key, None)
        assert schema_value == value, (
            f"Campo '{key}' esperado: {value}, obtido: {schema_value}"
        )


def assert_schema_creation_fails(
    schema_cls: Type[BaseModel], data: dict[str, Any]
) -> None:
    with pytest.raises(ValidationError):
        schema_cls(**data)


def assert_missing_required_fields(schema_cls: Type[BaseModel]) -> None:
    with pytest.raises(ValidationError):
        schema_cls(**{})


def assert_schema_from_orm(
    schema_cls: Type[BaseModel], instance: object
) -> None:
    # Validação via objeto (from_attributes=True)
    schema_from_obj = schema_cls.model_validate(instance)
    assert isinstance(schema_from_obj, schema_cls)

    for key, value in schema_from_obj.model_dump().items():
        assert value == getattr(instance, key), (
            f"[from_obj] Campo '{key}' esperado: "
            f"{getattr(instance, key)}, obtido: {value}"
        )

    # Validação via dict (como entrada externa)
    schema_from_dict = schema_cls.model_validate(instance.__dict__)
    assert isinstance(schema_from_dict, schema_cls)

    for key, value in schema_from_dict.model_dump().items():
        assert value == getattr(instance, key), (
            f"[from_dict] Campo '{key}' esperado: "
            f"{getattr(instance, key)}, obtido: {value}"
        )


def assert_partial_schema_with_none_fields(
    schema_cls: Type[BaseModel], partial_field: str, valid_data: dict[str, Any]
) -> None:
    value = valid_data[partial_field]
    schema = schema_cls(**{partial_field: value})
    assert getattr(schema, partial_field) == value

    for key in valid_data:
        if key != partial_field:
            assert getattr(schema, key) is None


async def graphql_query(client, query: str, variables: Optional[dict] = None):
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    response = await client.post("/graphql", json=payload)
    return response
