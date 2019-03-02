import datetime
import functools
import json
import pathlib
import typing

from graphql import graphql
from graphql.error import GraphQLError, format_error as format_graphql_error
from pygments import highlight, lexers
from pygments.formatters import Terminal256Formatter
from starlette import status
from starlette.background import BackgroundTasks
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import ASGIInstance, Receive, Scope, Send

from .utils.graphql_lexer import GraphqlLexer


def _get_playground_template(request_path: str):
    here = pathlib.Path(__file__).parent
    templates_path = here / "templates"

    with open(templates_path / "playground.html") as f:
        template = f.read()

    return template.replace("{{REQUEST_PATH}}", request_path)


class GraphQLApp:
    def __init__(self, schema, playground: bool = True) -> None:
        self.schema = schema
        self.playground = playground

    def __call__(self, scope: Scope) -> ASGIInstance:
        return functools.partial(self.asgi, scope=scope)

    async def asgi(self, receive: Receive, send: Send, scope: Scope) -> None:
        request = Request(scope, receive=receive)
        response = await self.handle_graphql(request)
        await response(receive, send)

    def _debug_log(
        self, operation_name: str, query: str, variables: typing.Dict["str", typing.Any]
    ):
        if operation_name == "IntrospectionQuery":
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{now}]: {operation_name or 'No operation name'}")
        print(highlight(query, GraphqlLexer(), Terminal256Formatter()))

        if variables:
            variables_json = json.dumps(variables, indent=4)

            print(highlight(variables_json, lexers.JsonLexer(), Terminal256Formatter()))

    async def handle_graphql(self, request: Request) -> Response:
        if request.method in ("GET", "HEAD"):
            if "text/html" in request.headers.get("Accept", ""):
                if not self.playground:
                    return PlainTextResponse(
                        "Not Found", status_code=status.HTTP_404_NOT_FOUND
                    )
            return await self.handle_playground(request)

        elif request.method == "POST":
            content_type = request.headers.get("Content-Type", "")

            if "application/json" in content_type:
                data = await request.json()
            elif "application/graphql" in content_type:
                body = await request.body()
                text = body.decode()
                data = {"query": text}
            elif "query" in request.query_params:
                data = request.query_params
            else:
                return PlainTextResponse(
                    "Unsupported Media Type",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )
        else:
            return PlainTextResponse(
                "Method Not Allowed", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")
        except KeyError:
            return PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        self._debug_log(operation_name, query, variables)

        background = BackgroundTasks()
        context = {"request": request, "background": background}

        result = await self.execute(
            query, variables=variables, context=context, operation_name=operation_name
        )
        error_data = (
            [format_graphql_error(err) for err in result.errors]
            if result.errors
            else None
        )
        response_data = {"data": result.data, "errors": error_data}
        status_code = (
            status.HTTP_400_BAD_REQUEST if result.errors else status.HTTP_200_OK
        )

        return JSONResponse(
            response_data, status_code=status_code, background=background
        )

    async def execute(self, query, variables=None, context=None, operation_name=None):
        return await graphql(
            self.schema,
            query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=context,
        )

    async def handle_playground(self, request: Request) -> Response:
        text = _get_playground_template(request.url.path)

        return HTMLResponse(text)
