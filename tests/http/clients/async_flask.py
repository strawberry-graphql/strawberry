from __future__ import annotations

from typing import Any, Optional

from flask import Flask
from flask import Request as FlaskRequest
from flask import Response as FlaskResponse
from strawberry.flask.views import AsyncGraphQLView as BaseAsyncGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.types import ExecutionResult
from tests.http.context import get_context
from tests.views.schema import Query, schema

from .base import ResultOverrideFunction
from .flask import FlaskHttpClient


class GraphQLView(BaseAsyncGraphQLView[dict[str, object], object]):
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]

    result_override: ResultOverrideFunction = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override")
        super().__init__(*args, **kwargs)

    async def get_root_value(self, request: FlaskRequest) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()

    async def get_context(
        self, request: FlaskRequest, response: FlaskResponse
    ) -> dict[str, object]:
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: FlaskRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class AsyncFlaskHttpClient(FlaskHttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ):
        self.app = Flask(__name__)
        self.app.debug = True

        view = GraphQLView.as_view(
            "graphql_view",
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )

        self.app.add_url_rule(
            "/graphql",
            view_func=view,
        )
