from typing import Dict

import pytest
from faker import Faker
from httpx import AsyncClient

faker = Faker()


class TestBaseGraphQL:
    async def _graphql_post(
        self, graphql_client: AsyncClient, query: str, variables: dict
    ) -> Dict:
        response = await graphql_client.post(
            "/graphql",
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200, response.text

        cookies = response.cookies.get("session")
        if cookies:
            graphql_client.cookies.set("session", cookies)

        return response.json()

    async def graphql_success(
        self, graphql_client: AsyncClient, query: str, variables: Dict = {}
    ):
        body = await self._graphql_post(graphql_client, query, variables)
        assert "errors" not in body, body
        return body["data"]

    async def graphql_expect_error(
        self, graphql_client: AsyncClient, query: str, variables: Dict = {}
    ):
        body = await self._graphql_post(graphql_client, query, variables)
        assert "errors" in body, body
        return body["errors"]

    def build_mutation(
        self,
        mutation_name: str,
        input_type: str,
        resolver_name: str,
        fields: str,
    ) -> str:
        if not fields:
            return f"""
                mutation {mutation_name}($input: {input_type}) {{
                    {resolver_name}(data: $input)
                }}
            """
        return f"""
            mutation {mutation_name}($input: {input_type}) {{
                {resolver_name}(data: $input) {{
                    {fields}
                }}
            }}
        """

    def build_query(self, query_name: str, fields: str) -> str:
        return f"""
            query {{
                {query_name} {{
                    {fields}
                }}
            }}
        """


class TestGraphQLWithUser(TestBaseGraphQL):
    @pytest.fixture
    async def user_service(self, graphql_context):
        service = graphql_context.user_service
        try:
            yield service
        finally:
            await graphql_context.session.rollback()
            await graphql_context.session.close()

    def strong_password(self) -> str:
        return faker.password(
            length=8,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True,
        )

    def mutation_create_user(self) -> str:
        return self.build_mutation(
            mutation_name="CreateUser",
            input_type="UserCreateInput!",
            resolver_name="createUser",
            fields="id name username email isMaster",
        )

    def mutation_login_user(self) -> str:
        return self.build_mutation(
            mutation_name="Login",
            input_type="UserLoginInput!",
            resolver_name="login",
            fields="name username isMaster",
        )

    def mutation_update_user(self) -> str:
        return self.build_mutation(
            mutation_name="UpdateUser",
            input_type="UserUpdateInput!",
            resolver_name="updateUser",
            fields="name username email",
        )

    def mutation_change_password(self) -> str:
        return self.build_mutation(
            mutation_name="ChangePassword",
            input_type="UserChangePasswordInput!",
            resolver_name="changePassword",
            fields="id isMaster",
        )

    def mutation_delete_user(self) -> str:
        return self.build_mutation(
            mutation_name="DeleteUser",
            input_type="UserDeleteInput!",
            resolver_name="deleteUser",
            fields="",
        )

    def _input_create_user(self) -> Dict[str, str]:
        return {
            "name": faker.name(),
            "username": faker.first_name(),
            "email": faker.email(),
            "password": self.strong_password(),
        }

    def _input_login_user(self, user_input: Dict[str, str]) -> Dict[str, str]:
        return {
            "email": user_input["email"],
            "password": user_input["password"],
        }

    @pytest.fixture
    def fixture_create_user(self):
        async def _create_user(graphql_client) -> Dict[str, str]:
            mutation = self.mutation_create_user()
            variables = {"input": self._input_create_user()}
            body = await self.graphql_success(
                graphql_client, mutation, variables
            )
            data = body["createUser"]
            data["password"] = variables["input"]["password"]

            return data

        return _create_user

    @pytest.fixture
    def fixture_login_user(self):
        async def _login_user(
            graphql_client, user_input: Dict[str, str]
        ) -> Dict[str, str]:
            mutation = self.mutation_login_user()
            variables = {"input": self._input_login_user(user_input)}
            body = await self.graphql_success(
                graphql_client, mutation, variables
            )
            assert "login" in body, body
            return body["login"]

        return _login_user
