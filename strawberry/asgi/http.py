import typing

from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response

from .utils import get_graphiql_html


async def get_http_response(
    request: Request,
    execute: typing.Callable,
    process_result: typing.Callable,
    graphiql: bool,
    root_value: typing.Optional[typing.Any],
    context: typing.Optional[typing.Any],
) -> Response:
    if request.method == "GET":
        if not graphiql:
            return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND)

        html = get_graphiql_html()
        return HTMLResponse(html)

    if request.method == "POST":
        content_type = request.headers.get("Content-Type", "")

        if "application/json" in content_type:
            data = await request.json()
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
        query = data["query"]
        variables = data.get("variables")
        operation_name = data.get("operationName")
    except KeyError:
        return PlainTextResponse(
            "No GraphQL query found in the request",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    result = await execute(
        query,
        variables=variables,
        context=context,
        operation_name=operation_name,
        root_value=root_value,
    )

    response_data = await process_result(request=request, result=result)

    return JSONResponse(response_data, status_code=status.HTTP_200_OK)
