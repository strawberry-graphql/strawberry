from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Optional, Union

from lia import ChaliceHTTPRequestAdapter, HTTPException

from chalice.app import Request, Response
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
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
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

    def get_root_value(self, request: Request) -> Optional[RootValue]:
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
        response_data: Union[GraphQLHTTPResponse, list[GraphQLHTTPResponse]],
        sub_response: TemporalResponse,
    ) -> Response:
        status_code = 200

        if sub_response.status_code != 200:
            status_code = sub_response.status_code

        return Response(
            body=self.encode_json(response_data),
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
            )


__all__ = ["GraphQLView"]
