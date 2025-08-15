import pytest
from faker import Faker

from app.utils.error_code import ErrorCode
from tests.utils.base_graphql_test import TestGraphQLWithUser

faker = Faker()


@pytest.mark.anyio
class TestUserMutation(TestGraphQLWithUser):
    async def test_create_user_success(self, graphql_client):
        mutation = self.mutation_create_user()
        variables = {"input": self._input_create_user()}

        response = await self.graphql_success(
            graphql_client, mutation, variables
        )

        data = response["createUser"]
        assert data["id"] is not None
        assert data["name"] == variables["input"]["name"]
        assert data["email"] == variables["input"]["email"]
        assert data["username"] == variables["input"]["username"]
        assert data["isMaster"] is False

    @pytest.mark.parametrize(
        "field", ["name", "username", "email", "password"]
    )
    async def test_create_user_failure_missing_required_fields(
        self, graphql_client, field
    ):
        input = self._input_create_user()
        input.pop(field)

        variables = {"input": input}
        mutation = self.mutation_create_user()

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.MISSING_REQUIRED_INPUT, response
        assert field in error["details"], response

    @pytest.mark.parametrize(
        "override",
        [{"name": "no"}, {"username": ("A" * 65)}, {"email": "invalid-email"}],
    )
    async def test_create_user_failure_invalid_value(
        self, graphql_client, override
    ):
        input = self._input_create_user()
        input.update(**override)

        variables = {"input": input}
        mutation = self.mutation_create_user()

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.INVALID_ARGUMENT_VALUE, response
        assert "".join(override.keys()) in error["details"], response

    @pytest.mark.parametrize(
        "override",
        [
            124,
            "invalidpassword",
            "invalidp@ssword",
            "invalidPassword",
            "InvalidP@ssword",
            "1nv4l1dp4ssw0rd",
        ],
    )
    async def test_create_user_failure_invalid_value_password(
        self, graphql_client, override
    ):
        input = self._input_create_user()
        input.update(password=override)

        variables = {"input": input}
        mutation = self.mutation_create_user()

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        if isinstance(override, int):
            assert error["code"] == ErrorCode.INVALID_ARGUMENT_TYPE, response
        else:
            assert error["code"] == ErrorCode.INVALID_ARGUMENT_VALUE, response

    @pytest.mark.parametrize(
        "override, code_erro",
        [
            ({"username": "Rei Arthur"}, "DuplicateUsernameError"),
            ({"email": "example@example.com"}, "DuplicateEmailError"),
        ],
    )
    async def test_create_user_failure_unique_value_field(
        self, graphql_client, override, code_erro
    ):
        input = self._input_create_user()
        input.update(**override)

        variables = {"input": input}
        mutation = self.mutation_create_user()

        await self.graphql_success(graphql_client, mutation, variables)

        new_input = self._input_create_user()
        new_input.update(**override)
        new_variables = {"input": new_input}

        response = await self.graphql_expect_error(
            graphql_client, mutation, new_variables
        )

        error = response[0]
        assert error["code"] == code_erro, response
        assert "".join(override.values()) in error["message"], response

    async def test_login_user_success(
        self, graphql_client, fixture_create_user
    ):
        user = await fixture_create_user(graphql_client)
        mutation = self.mutation_login_user()
        variables = {
            "input": {"email": user["email"], "password": user["password"]}
        }

        response = await self.graphql_success(
            graphql_client, mutation, variables
        )
        data = response["login"]
        assert data["name"] == user["name"], data

    @pytest.mark.parametrize(
        "override, code_error",
        [
            ({"email": faker.email()}, "UserNotFoundError"),
            ({"password": faker.password()}, "InvalidCredentialsError"),
        ],
    )
    async def test_login_user_failure_invalid_credentials(
        self, graphql_client, fixture_create_user, override, code_error
    ):
        user = await fixture_create_user(graphql_client)

        mutation = self.mutation_login_user()
        variables = {
            "input": {"email": user["email"], "password": user["password"]}
        }
        variables["input"].update(override)

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )
        assert response[0]["code"] == code_error, response

    @pytest.mark.parametrize("field", ["email", "password"])
    async def test_login_user_failure_missing_fields(
        self, graphql_client, fixture_create_user, field
    ):
        user = await fixture_create_user(graphql_client)

        input = {"email": user["email"], "password": user["password"]}
        input.pop(field)
        variables = {"input": input}
        mutation = self.mutation_login_user()

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.MISSING_REQUIRED_INPUT, response
        assert field in error["details"], response

    async def test_login_user_failure_extra_field(
        self, graphql_client, fixture_create_user
    ):
        user = await fixture_create_user(graphql_client)

        mutation = self.mutation_login_user()
        variables = {
            "input": {
                "email": user["email"],
                "password": user["password"],
                "extraField": "unexpected_value",
            }
        }

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.UNEXPECTED_INPUT, response
        assert "extraField" in error["details"], response

    @pytest.mark.parametrize(
        "field, value",
        [
            ("name", "Rei Arthur"),
            ("username", "Rei Arthur"),
            ("email", "rei.arthur@example.com"),
        ],
    )
    async def test_update_user_success_one_field(
        self,
        graphql_client,
        fixture_create_user,
        fixture_login_user,
        field,
        value,
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_update_user()
        variables = {"input": {field: value, "password": user["password"]}}

        response = await self.graphql_success(
            graphql_client, mutation, variables
        )
        data = response["updateUser"]

        for key in ["name", "username", "email"]:
            if key == field:
                assert data[key] == value, (
                    f"Expected {key} to be {value}, got {data[key]}"
                )
            else:
                assert data[key] == user[key], (
                    f"Expected {key} to remain unchanged, got {data[key]}"
                )

    async def test_update_user_success_multiple_fields(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_update_user()
        variables = {
            "input": {
                "name": "Rei Arthur",
                "username": "Rei Arthur",
                "password": user["password"],
            }
        }

        response = await self.graphql_success(
            graphql_client, mutation, variables
        )

        data = response["updateUser"]
        assert data["name"] == "Rei Arthur", data
        assert data["username"] == "Rei Arthur", data
        assert data["email"] == user["email"], data

    async def test_update_user_failure_not_authenticated(self, graphql_client):
        mutation = self.mutation_update_user()
        variables = {
            "input": {
                "name": "Rei Arthur",
                "username": "Rei Arthur",
                "password": "validPassword123",
            }
        }

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )
        assert response[0]["code"] == "PermissionDeniedError", response

    async def test_update_user_failure_missing_fields(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_update_user()
        variables = {"input": {"password": user["password"]}}

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.INVALID_ARGUMENT_VALUE, response

    async def test_update_user_failure_missing_password(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_update_user()
        variables = {"input": {"name": "Rei Arthur"}}

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.MISSING_REQUIRED_INPUT, response
        assert "password" in error["details"], response

    async def test_update_user_failure_extra_field(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_update_user()
        variables = {"input": {"isMaster": True, "password": user["password"]}}

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.UNEXPECTED_INPUT, response
        assert "isMaster" in error["details"], response

    async def test_change_password_success(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_change_password()
        variables = {
            "input": {
                "currentPassword": user["password"],
                "newPassword": self.strong_password(),
            }
        }

        response = await self.graphql_success(
            graphql_client, mutation, variables
        )

        data = response["changePassword"]
        assert data["id"] == user["id"], data
        assert data["isMaster"] == user["isMaster"], data

    async def test_change_password_failure_not_authenticated(
        self, graphql_client
    ):
        mutation = self.mutation_change_password()
        variables = {
            "input": {
                "currentPassword": "oldP@ssword123",
                "newPassword": "newStrongP@ssword123",
            }
        }

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )
        assert response[0]["code"] == "PermissionDeniedError", response

    async def test_change_password_failure_invalid_current_password(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_change_password()
        variables = {
            "input": {
                "currentPassword": self.strong_password(),
                "newPassword": self.strong_password(),
            }
        }

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )
        assert response[0]["code"] == "InvalidCredentialsError", response

    @pytest.mark.parametrize("field", ["currentPassword", "newPassword"])
    async def test_change_password_failure_missing_fields(
        self, graphql_client, fixture_create_user, fixture_login_user, field
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        input = {
            "currentPassword": user["password"],
            "newPassword": self.strong_password(),
        }
        input.pop(field)
        variables = {"input": input.copy()}
        mutation = self.mutation_change_password()

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.MISSING_REQUIRED_INPUT, response
        assert field in error["details"], response

    async def test_change_password_failure_extra_field(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_change_password()
        variables = {
            "input": {
                "currentPassword": user["password"],
                "newPassword": self.strong_password(),
                "isMaster": True,
            }
        }

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.UNEXPECTED_INPUT, response
        assert "isMaster" in error["details"], response

    async def test_change_password_failure_invalid_new_password(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_change_password()
        variables = {
            "input": {
                "currentPassword": user["password"],
                "newPassword": "weakpassword",
            }
        }

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.INVALID_ARGUMENT_VALUE, response
        assert "new_password" in error["details"], response

    async def test_delete_user_success(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_delete_user()
        variables = {"input": {"password": user["password"]}}

        response = await self.graphql_success(
            graphql_client, mutation, variables
        )

        data = response["deleteUser"]
        assert data is True, data

    async def test_delete_user_failure_not_authenticated(self, graphql_client):
        mutation = self.mutation_delete_user()
        variables = {"input": {"password": "validPassword123"}}

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )
        assert response[0]["code"] == "PermissionDeniedError", response

    async def test_delete_user_failure_invalid_password(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_delete_user()
        variables = {"input": {"password": "invalidPassword"}}

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )
        assert response[0]["code"] == "InvalidCredentialsError", response

    async def test_delete_user_failure_missing_password(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_delete_user()
        variables = {"input": {}}

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.MISSING_REQUIRED_INPUT, response
        assert "password" in error["details"], response

    async def test_delete_user_failure_extra_field(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        mutation = self.mutation_delete_user()
        variables = {
            "input": {"password": user["password"], "extraField": "value"}
        }

        response = await self.graphql_expect_error(
            graphql_client, mutation, variables
        )

        error = response[0]
        assert error["code"] == ErrorCode.UNEXPECTED_INPUT, response
        assert "extraField" in error["details"], response
