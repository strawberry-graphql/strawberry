from __future__ import annotations

from typing import Dict

from flask import Flask
from flask import Response as FlaskResponse
from strawberry.flask.views import AsyncGraphQLView as BaseAsyncGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from tests.views.schema import Query, schema

from ..context import get_context
from . import ResultOverrideFunction
from .flask import FlaskHttpClient


class GraphQLView(BaseAsyncGraphQLView):
    # this allows to test our code path for checking the request type
    # TODO: we might want to remove our check since it is done by flask
    # already
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]

    result_override: ResultOverrideFunction = None

    def __init__(self, *args, **kwargs):
        self.result_override = kwargs.pop("result_override")
        super().__init__(*args, **kwargs)

    async def get_root_value(self):
        return Query()

    async def get_context(self, response: FlaskResponse) -> Dict[str, object]:
        context = await super().get_context(response)

        return get_context(context)

    async def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(result)


class AsyncFlaskHttpClient(FlaskHttpClient):
    def __init__(
        self,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        self.app = Flask(__name__)
        self.app.debug = True

        view = GraphQLView.as_view(
            "graphql_view",
            schema=schema,
            graphiql=graphiql,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
        )

        self.app.add_url_rule(
            "/graphql",
            view_func=view,
        )
