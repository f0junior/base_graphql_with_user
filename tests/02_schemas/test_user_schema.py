from typing import Any, Dict

import pytest
from faker import Faker
from pydantic import ValidationError

from app.schemas.user_schema import (
    UserChangePassword,
    UserCreate,
    UserDelete,
    UserLogin,
    UserRead,
    UserUpdate,
)
from tests import helpers

faker = Faker()


def valid_password() -> str:
    return faker.password(
        length=8,
        special_chars=True,
        digits=True,
        upper_case=True,
        lower_case=True,
    )


@pytest.fixture
def strong_password() -> str:
    return valid_password()


def default_valid_data(**kwargs) -> Dict[str, Any]:
    data = {
        "name": faker.name(),
        "username": faker.first_name(),
        "email": faker.email(),
        "password": valid_password(),
    }
    data.update(**kwargs)

    return data


def test_user_create_success():
    helpers.assert_schema_equals_data(UserCreate, default_valid_data())


def test_user_create_failure_none_value():
    helpers.assert_missing_required_fields(UserCreate)


@pytest.mark.parametrize(
    "override",
    [
        {"name": "no"},
        {"username": "no"},
        {"email": "invalid-email"},
        {"password": "invalid-password"},
    ],
)
def test_user_create_failure_invalid_value(override):
    helpers.assert_schema_creation_fails(
        UserCreate, default_valid_data(**override)
    )


@pytest.mark.parametrize(
    "override",
    [{"name": 123}, {"username": True}, {"email": 123}, {"password": 123}],
)
def test_user_create_failure_wrong_type(override):
    with pytest.raises(Exception) as exc:
        UserCreate(**default_valid_data(**override))
    assert isinstance(exc.value, ValidationError)


def test_user_create_failure_extra_field():
    helpers.assert_schema_creation_fails(
        UserCreate, default_valid_data(is_master=True)
    )


@pytest.mark.parametrize("data_update", ["name", "username", "email"])
def test_user_update_success(data_update):
    full_data = default_valid_data()
    data = {k: full_data[k] for k in (data_update, "password")}
    schema = UserUpdate(**data)

    assert getattr(schema, data_update) == data.get(data_update)

    for key in full_data.keys():
        if key not in (data_update, "password"):
            assert getattr(schema, key) is None


@pytest.mark.parametrize(
    "override",
    [
        {"name": "no"},
        {"username": "no"},
        {"email": "invalid-email"},
    ],
)
def test_user_update_failure_invalid_value(override):
    data = {"password": valid_password(), **override}
    helpers.assert_schema_creation_fails(UserUpdate, data)


@pytest.mark.parametrize(
    "override",
    [{"name": 123}, {"username": True}, {"email": 123}, {"password": 123}],
)
def test_user_update_failure_wrong_type(override):
    helpers.assert_schema_creation_fails(
        UserUpdate, default_valid_data(**override)
    )


def test_user_update_failure_not_informed_password():
    data = default_valid_data()
    data.pop("password")

    helpers.assert_schema_creation_fails(UserUpdate, data)


def test_user_update_failure_invalid_password():
    helpers.assert_schema_creation_fails(
        UserUpdate, default_valid_data(password="invalid-password")
    )


def test_user_update_failure_extra_field():
    helpers.assert_schema_creation_fails(
        UserUpdate, default_valid_data(is_master=True)
    )


def test_user_update_failure_not_informed_value(strong_password):
    helpers.assert_schema_creation_fails(
        UserUpdate, {"password": strong_password}
    )


def test_user_change_password_success(strong_password):
    data = {
        "current_password": strong_password,
        "new_password": valid_password(),
    }
    helpers.assert_schema_equals_data(UserChangePassword, data)


def test_user_change_password_failure_equal_password(strong_password):
    data = {
        "current_password": strong_password,
        "new_password": strong_password,
    }

    helpers.assert_schema_creation_fails(UserChangePassword, data)


def test_user_change_password_failure_invalid_password(strong_password):
    data = {
        "current_password": strong_password,
        "new_password": "invalid-password",
    }

    helpers.assert_schema_creation_fails(UserChangePassword, data)


@pytest.mark.parametrize("override", ["current_password", "new_password"])
def test_user_change_password_failure_wrong_value(override, strong_password):
    data = {"current_password": 123, "new_password": True}
    data.update(**{override: strong_password})

    helpers.assert_schema_creation_fails(UserChangePassword, data)


def test_user_change_password_failure_extra_field(strong_password):
    data = {
        "current_password": strong_password,
        "new_password": valid_password(),
        "is_master": True,
    }

    helpers.assert_schema_creation_fails(UserChangePassword, data)


def test_user_login_success(strong_password):
    data = {"email": "example@example.com", "password": strong_password}

    helpers.assert_schema_equals_data(UserLogin, data)


@pytest.mark.parametrize(
    "override", [{"email": "invalid-email"}, {"password": "invalid-password"}]
)
def test_user_login_failure_invalid_value(override, strong_password):
    data = {"email": "example@example.com", "password": strong_password}
    data.update(**override)

    helpers.assert_schema_creation_fails(UserLogin, data)


def test_user_login_failure_not_informed_value():
    helpers.assert_missing_required_fields(UserLogin)


@pytest.mark.parametrize("override", [{"email": 123}, {"password": True}])
def test_user_login_failure_wrong_type(override, strong_password):
    data = {"email": "example@example.com", "password": strong_password}
    data.update(override)

    helpers.assert_schema_creation_fails(UserLogin, data)


def test_user_login_failure_extra_field():
    data = {
        "email": "example@example.com",
        "password": strong_password,
        "is_master": True,
    }

    helpers.assert_schema_creation_fails(UserLogin, data)


def test_user_delete_success(strong_password):
    data = {"password": strong_password}
    helpers.assert_schema_equals_data(UserDelete, data)


def test_user_delete_failure_extra_field(strong_password):
    data = {
        "password": strong_password,
        "is_master": True,
    }
    helpers.assert_schema_creation_fails(UserDelete, data)


def test_user_delete_failure_not_informed_value():
    helpers.assert_missing_required_fields(UserDelete)


def test_user_read_from_orm_success():
    class FakerUser(helpers.FakeWithID):
        pass

    data = default_valid_data(is_master=False)
    data.pop("password")

    instance = FakerUser(**data)
    helpers.assert_schema_from_orm(UserRead, instance)
