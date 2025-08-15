from starlette.requests import Request
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from app.utils.graphql_error_formatter import GraphQLErrorFormatter


class CustomGraphQLRouter(GraphQLRouter):
    def __init__(self, schema, **kwargs):
        self.error_formatter = GraphQLErrorFormatter()
        super().__init__(schema, **kwargs)

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {}
        if result.data is not None:
            data["data"] = result.data

        if result.errors is not None:
            data["errors"] = self.error_formatter.format_all(result.errors)

        return data
