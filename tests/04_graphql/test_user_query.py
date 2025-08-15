from uuid import UUID

import pytest
from faker import Faker

from app.schemas.user_schema import UserDelete
from app.utils.error_code import ErrorCode
from tests.utils.base_graphql_test import TestGraphQLWithUser

faker = Faker()


@pytest.mark.anyio
class TestUserQuery(TestGraphQLWithUser):
    async def test_me_success(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        query = self.build_query(query_name="me", fields="id name email")
        response = await self.graphql_success(graphql_client, query)

        data = response["me"]
        assert data is not None
        assert data["id"] == user["id"]
        assert data["name"] == user["name"]
        assert data["email"] == user["email"]

    async def test_me_failure_not_authenticated(self, graphql_client):
        query = self.build_query(query_name="me", fields="id name email")
        response = await self.graphql_expect_error(graphql_client, query, {})

        assert response[0]["code"] == "PermissionDeniedError", response

    async def test_me_failure_session_invalid(self, graphql_client):
        graphql_client.cookies["session"] = "faker.uuid4()"

        query = self.build_query(query_name="me", fields="id name email")
        response = await self.graphql_expect_error(graphql_client, query)
        assert response[0]["code"] == "ExpiredSessionError", response

    async def test_me_failure_user_not_found(
        self,
        graphql_client,
        fixture_create_user,
        fixture_login_user,
        user_service,
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        await user_service.delete_user(
            UUID(user.get("id")), UserDelete(password=user.get("password"))
        )

        query = self.build_query(query_name="me", fields="id name email")
        response = await self.graphql_expect_error(graphql_client, query)

        assert response[0]["code"] == "UserNotFoundError", response

    async def test_me_failure_field_not_exist(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        query = self.build_query(query_name="me", fields="id name email teste")
        response = await self.graphql_expect_error(graphql_client, query)

        error = response[0]
        assert error["code"] == ErrorCode.INVALID_QUERY_FIELD, response
        assert "teste" in error["details"], response

    async def test_logout_success(
        self, graphql_client, fixture_create_user, fixture_login_user
    ):
        user = await fixture_create_user(graphql_client)
        await fixture_login_user(graphql_client, user)

        query = self.build_query(query_name="logout", fields="success")
        response = await self.graphql_success(graphql_client, query)

        data = response["logout"]
        assert data is not None, response
        assert data["success"] is True, data

        query_me = self.build_query(query_name="me", fields="id name email")
        await self.graphql_expect_error(graphql_client, query_me)

    async def test_logout_failure_valid_but_nonexistent_session(
        self, graphql_client
    ):
        graphql_client.cookies["session"] = faker.uuid4()

        query = self.build_query(query_name="logout", fields="success")
        response = await self.graphql_expect_error(graphql_client, query)
        assert response[0]["code"] == "ExpiredSessionError", response

    async def test_logout_failure_session_invalid(self, graphql_client):
        graphql_client.cookies["session"] = "faker.uuid4()"

        query = self.build_query(query_name="logout", fields="success")
        response = await self.graphql_expect_error(graphql_client, query)
        assert response[0]["code"] == "ExpiredSessionError", response
