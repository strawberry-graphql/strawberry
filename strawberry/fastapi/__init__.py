from typing import Any, Dict, Optional

from pydantic import Field

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocket
from strawberry.asgi import GraphQL
from strawberry.asgi.utils import get_graphiql_html
from strawberry.http import GraphQLHTTPResponse, GraphQLRequestData, process_result
from strawberry.utils.debug import pretty_print_graphql_operation


NO_GRAPHIQL_MSG = "GraphiQL not enabled"
GRAPHIQL_EXAMPLE = """
<!DOCTYPE html>
<html>
<head>
    <title>Strawberry GraphiQL</title>
    ...
</head>
<body>
    ...
</body>
</html>
"""


class GraphQLRequestDataPydantic(GraphQLRequestData):
    variables: Optional[Dict[str, Any]] = None
    operation_name: Optional[str] = Field(None, alias="operationName")


def GraphQLRouter(*args, **kwargs) -> APIRouter:
    graphql = GraphQL(*args, **kwargs)

    router = APIRouter()

    @router.get(
        "",
        response_class=HTMLResponse,
        responses={
            200: {
                "content": {
                    "text/html": {"example": GRAPHIQL_EXAMPLE},
                },
                "description": "The GraphiQL integrated development environment.",
            },
            404: {
                "content": {
                    "application/json": {"example": {"detail": NO_GRAPHIQL_MSG}},
                },
                "description": "Error if GraphiQL is not enabled.",
            },
        },
    )
    def graphql_get():
        """Return the GraphiQL integrated development environment."""
        if not graphql.graphiql:
            raise HTTPException(status_code=404, detail=NO_GRAPHIQL_MSG)
        return HTMLResponse(get_graphiql_html())

    @router.post(
        "",
        response_model=GraphQLHTTPResponse,
        responses={
            200: {
                "content": {
                    "application/json": {
                        "examples": {
                            "normal": {
                                "summary": "Data query response",
                                "description": "A data query response.",
                                "value": {
                                    "data": {"books": [{"title": "The Great Gatsby"}]}
                                },
                            },
                            "introspection": {
                                "summary": "Introspection query",
                                "description": "An introspection query response.",
                                "value": {
                                    "data": {
                                        "__schema": {"queryType": {"name": "Query"}}
                                    }
                                },
                            },
                        }
                    },
                },
                "description": "The GraphQL query response.",
            }
        },
    )
    async def graphql_post(
        request_data: GraphQLRequestDataPydantic = Body(
            ...,
            examples={
                "normal": {
                    "summary": "Data query",
                    "description": "A normal query to lookup data.",
                    "value": {"query": "query{books{title}}"},
                },
                "introspection": {
                    "summary": "Introspection query",
                    "description": "An introspection query to discover the schema.",
                    "value": {"query": "query{__schema{queryType{name}}}"},
                },
            },
        )
    ):
        if graphql.debug:
            pretty_print_graphql_operation(
                request_data.operation_name, request_data.query, request_data.variables
            )

        result = await graphql.schema.execute(
            request_data.query,
            root_value=None,
            variable_values=request_data.variables,
            operation_name=request_data.operation_name,
            context_value={},
        )
        return process_result(result=result)

    @router.websocket("")
    async def graphql_websocket(ws: WebSocket):
        await graphql.handle_websocket(ws)

    return router
