from __future__ import annotations

from io import BytesIO
from json import dumps
from typing import Any, Optional, Union
from typing_extensions import Literal

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpRequest, HttpResponse
from django.test.client import RequestFactory

from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.types import ExecutionResult
from tests.http.context import get_context
from tests.views.schema import Query, schema

from .base import JSON, HttpClient, Response, ResultOverrideFunction


class GraphQLView(BaseGraphQLView[dict[str, object], object]):
    result_override: ResultOverrideFunction = None

    def get_root_value(self, request) -> Query:
        super().get_root_value(request)  # for coverage
        return Query()

    def get_context(
        self, request: HttpRequest, response: HttpResponse
    ) -> dict[str, object]:
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
        multipart_uploads_enabled: bool = False,
    ):
        self.view = GraphQLView.as_view(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )

    def _get_header_name(self, key: str) -> str:
        return f"HTTP_{key.upper().replace('-', '_')}"

    def _to_django_headers(self, headers: dict[str, str]) -> dict[str, str]:
        return {self._get_header_name(key): value for key, value in headers.items()}

    def _get_headers(
        self,
        method: Literal["get", "post"],
        headers: Optional[dict[str, str]],
        files: Optional[dict[str, BytesIO]],
    ) -> dict[str, str]:
        headers = headers or {}
        headers = self._to_django_headers(headers)

        return super()._get_headers(method=method, headers=headers, files=files)

    async def _do_request(self, request: HttpRequest) -> Response:
        try:
            response = self.view(request)
        except Http404:
            return Response(status_code=404, data=b"Not found")
        except (BadRequest, SuspiciousOperation) as e:
            return Response(status_code=400, data=e.args[0].encode())
        else:
            return Response(
                status_code=response.status_code,
                data=response.content,
                headers=dict(response.headers),
            )

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[dict[str, object]] = None,
        files: Optional[dict[str, BytesIO]] = None,
        headers: Optional[dict[str, str]] = None,
        extensions: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        headers = self._get_headers(method=method, headers=headers, files=files)
        additional_arguments = {**kwargs, **headers}

        body = self._build_body(
            query=query,
            variables=variables,
            files=files,
            method=method,
            extensions=extensions,
        )

        data: Union[dict[str, object], str, None] = None

        if body and files:
            body.update(
                {
                    name: SimpleUploadedFile(name, file.read())
                    for name, file in files.items()
                }
            )
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
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        headers = headers or {}

        factory = RequestFactory()
        request = getattr(factory, method)(url, **headers)

        return await self._do_request(request)

    async def get(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        django_headers = self._to_django_headers(headers or {})
        return await self.request(url, "get", headers=django_headers)

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        django_headers = self._to_django_headers(headers or {})
        content_type = django_headers.pop("HTTP_CONTENT_TYPE", "")

        body = data or dumps(json)

        factory = RequestFactory()
        request = factory.post(
            url,
            data=body,
            content_type=content_type,
            headers=django_headers,
        )

        return await self._do_request(request)
