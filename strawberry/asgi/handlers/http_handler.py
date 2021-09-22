import json
from typing import Any, Callable, Optional

from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import Receive, Scope, Send

from strawberry.asgi.utils import get_graphiql_html
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import parse_request_data
from strawberry.schema import BaseSchema
from strawberry.utils.debug import pretty_print_graphql_operation


class HTTPHandler:
    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool,
        debug: bool,
        get_context,
        get_root_value,
        process_result,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.debug = debug
        self.get_context = get_context
        self.get_root_value = get_root_value
        self.process_result = process_result

    async def handle(self, scope: Scope, receive: Receive, send: Send):
        request = Request(scope=scope, receive=receive)
        root_value = await self.get_root_value(request)

        sub_response = Response(
            content=None,
            status_code=None,  # type: ignore
            headers=None,
            media_type=None,
            background=None,
        )

        context = await self.get_context(request=request, response=sub_response)

        response = await self.get_http_response(
            request=request,
            execute=self.execute,
            process_result=self.process_result,
            graphiql=self.graphiql,
            root_value=root_value,
            context=context,
        )

        response.headers.raw.extend(sub_response.headers.raw)

        if sub_response.background:
            response.background = sub_response.background

        if sub_response.status_code:
            response.status_code = sub_response.status_code

        await response(scope, receive, send)

    async def get_http_response(
        self,
        request: Request,
        execute: Callable,
        process_result: Callable,
        graphiql: bool,
        root_value: Optional[Any],
        context: Optional[Any],
    ) -> Response:
        if request.method == "GET":
            if not graphiql:
                return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND)

            return self.get_graphiql_response()

        if request.method == "POST":
            content_type = request.headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    data = await request.json()
                except json.JSONDecodeError:
                    return PlainTextResponse(
                        "Unable to parse request body as JSON",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
            elif content_type.startswith("multipart/form-data"):
                multipart_data = await request.form()
                operations = json.loads(multipart_data.get("operations", "{}"))
                files_map = json.loads(multipart_data.get("map", "{}"))

                data = replace_placeholders_with_files(
                    operations, files_map, multipart_data
                )

            else:
                return PlainTextResponse(
                    "Unsupported Media Type",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )
        else:
            return PlainTextResponse(
                "Method Not Allowed",
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            return PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        result = await execute(
            request_data.query,
            variables=request_data.variables,
            context=context,
            operation_name=request_data.operation_name,
            root_value=root_value,
        )

        response_data = await process_result(request=request, result=result)

        return JSONResponse(response_data, status_code=status.HTTP_200_OK)

    def get_graphiql_response(self) -> HTMLResponse:
        html = get_graphiql_html()

        return HTMLResponse(html)

    async def execute(
        self, query, variables=None, context=None, operation_name=None, root_value=None
    ):
        if self.debug:
            pretty_print_graphql_operation(operation_name, query, variables)

        return await self.schema.execute(
            query,
            root_value=root_value,
            variable_values=variables,
            operation_name=operation_name,
            context_value=context,
        )
