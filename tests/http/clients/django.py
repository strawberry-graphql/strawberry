from __future__ import annotations

from io import BytesIO
from json import dumps
from typing import Any, Dict, Optional, Union
from typing_extensions import Literal

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpRequest, HttpResponse
from django.test.client import RequestFactory

from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.types import ExecutionResult
from tests.views.schema import Query, schema

from ..context import get_context
from .base import JSON, HttpClient, Response, ResultOverrideFunction


class GraphQLView(BaseGraphQLView):
    result_override: ResultOverrideFunction = None

    def get_root_value(self, request) -> Query:
        super().get_root_value(request)  # for coverage
        return Query()

    def get_context(self, request: HttpRequest, response: HttpResponse) -> object:
        context = {"request": request, "response": response}

        return get_context(context)

    def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return super().process_result(request, result)


class DjangoHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        self.graphiql = graphiql
        self.graphql_ide = graphql_ide
        self.allow_queries_via_get = allow_queries_via_get
        self.result_override = result_override

    def _get_header_name(self, key: str) -> str:
        return f"HTTP_{key.upper().replace('-', '_')}"

    def _get_headers(
        self,
        method: Literal["get", "post"],
        headers: Optional[Dict[str, str]],
        files: Optional[Dict[str, BytesIO]],
    ) -> Dict[str, str]:
        headers = headers or {}
        headers = {self._get_header_name(key): value for key, value in headers.items()}

        return super()._get_headers(method=method, headers=headers, files=files)

    async def _do_request(self, request: RequestFactory) -> Response:
        view = GraphQLView.as_view(
            schema=schema,
            graphiql=self.graphiql,
            graphql_ide=self.graphql_ide,
            allow_queries_via_get=self.allow_queries_via_get,
            result_override=self.result_override,
        )

        try:
            response = view(request)
        except Http404:
            return Response(
                status_code=404, data=b"Not found", headers=response.headers
            )
        except (BadRequest, SuspiciousOperation) as e:
            return Response(
                status_code=400, data=e.args[0].encode(), headers=response.headers
            )
        else:
            return Response(
                status_code=response.status_code,
                data=response.content,
                headers=response.headers,
            )

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        extensions: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        headers = self._get_headers(method=method, headers=headers, files=files)
        additional_arguments = {**kwargs, **headers}

        body = self._build_body(
            query=query, variables=variables, files=files, method=method
        )

        data: Union[Dict[str, object], str, None] = None

        if body and files:
            files = {
                name: SimpleUploadedFile(name, file.read())
                for name, file in files.items()
            }
            body.update(files)
        else:
            additional_arguments["content_type"] = "application/json"

        if body:
            data = body if files or method == "get" else dumps(body)

        factory = RequestFactory()
        request = getattr(factory, method)(
            "/graphql",
            data=data,
            **additional_arguments,
        )

        return await self._do_request(request)

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        headers = self._get_headers(
            method=method,  # type: ignore
            headers=headers,
            files=None,
        )

        factory = RequestFactory()
        request = getattr(factory, method)(url, **headers)

        return await self._do_request(request)

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        return await self.request(url, "get", headers=headers)

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        headers = self._get_headers(method="post", headers=headers, files=None)

        additional_arguments = {**headers}

        body = data or dumps(json)

        if headers.get("HTTP_CONTENT_TYPE"):
            additional_arguments["content_type"] = headers["HTTP_CONTENT_TYPE"]

        factory = RequestFactory()
        request = factory.post(
            url,
            data=body,
            **additional_arguments,
        )

        return await self._do_request(request)
