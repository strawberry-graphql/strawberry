from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from chalice.app import Request, Response
from cross_web import ChaliceHTTPRequestAdapter, HTTPException

from strawberry.http.sync_base_view import SyncBaseHTTPView
from strawberry.http.temporal_response import TemporalResponse
from strawberry.http.typevars import Context, RootValue

if TYPE_CHECKING:
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema import BaseSchema


class GraphQLView(
    SyncBaseHTTPView[Request, Response, TemporalResponse, Context, RootValue]
):
    allow_queries_via_get: bool = True
    request_adapter_class = ChaliceHTTPRequestAdapter

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool | None = None,
        graphql_ide: GraphQL_IDE | None = "graphiql",
        allow_queries_via_get: bool = True,
    ) -> None:
        self.allow_queries_via_get = allow_queries_via_get
        self.schema = schema
        if graphiql is not None:
            warnings.warn(
                "The `graphiql` argument is deprecated in favor of `graphql_ide`",
                DeprecationWarning,
                stacklevel=2,
            )
            self.graphql_ide = "graphiql" if graphiql else None
        else:
            self.graphql_ide = graphql_ide

    def get_root_value(self, request: Request) -> RootValue | None:
        return None

    def render_graphql_ide(self, request: Request) -> Response:
        return Response(
            self.graphql_ide_html,
            headers={"Content-Type": "text/html"},
        )

    def get_sub_response(self, request: Request) -> TemporalResponse:
        return TemporalResponse()

    def get_context(self, request: Request, response: TemporalResponse) -> Context:
        return {"request": request, "response": response}  # type: ignore

    def create_response(
        self,
        response_data: GraphQLHTTPResponse | list[GraphQLHTTPResponse],
        sub_response: TemporalResponse,
    ) -> Response:
        status_code = 200

        if sub_response.status_code != 200:
            status_code = sub_response.status_code

        encoded_data = self.encode_json(response_data)
        if isinstance(encoded_data, bytes):
            encoded_data = encoded_data.decode()
        # Chalice expects str or objects for body unless the content type has been added to the chalice app
        # list of binary content types
        return Response(
            body=encoded_data,
            status_code=status_code,
            headers={
                "Content-Type": "application/json",
                **sub_response.headers,
            },
        )

    def execute_request(self, request: Request) -> Response:
        try:
            return self.run(request=request)
        except HTTPException as e:
            return Response(
                body=e.reason,
                status_code=e.status_code,
                headers={"Content-Type": "text/plain"},
            )


__all__ = ["GraphQLView"]
