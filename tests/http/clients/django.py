from __future__ import annotations

from io import BytesIO
from json import dumps
from typing import Dict, Optional, Union

from typing_extensions import Literal

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http.response import Http404
from django.test.client import RequestFactory

from strawberry.django.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    def get_root_value(self, request):
        return Query()


class DjangoHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True):
        self.graphiql = graphiql

    def _get_header_name(self, key: str) -> str:
        return f"HTTP_{key.upper().replace('-', '_')}"

    def _get_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        return {self._get_header_name(key): value for key, value in headers.items()}

    def _do_request(self, request: RequestFactory) -> Response:
        try:
            response = GraphQLView.as_view(schema=schema, graphiql=self.graphiql)(
                request
            )
        except Http404:
            return Response(status_code=404, data=b"Not found")
        except (BadRequest, SuspiciousOperation) as e:
            return Response(status_code=400, data=e.args[0].encode())
        else:
            return Response(status_code=response.status_code, data=response.content)

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        headers = self._get_headers(headers or {})
        additional_arguments = {**kwargs, **headers}

        body = self._build_body(query, variables, files)

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
            data = body if files else dumps(body)

        factory = RequestFactory()
        request = getattr(factory, method)(
            "/graphql",
            data=data,
            **additional_arguments,
        )

        return self._do_request(request)

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        headers = self._get_headers(headers or {})

        factory = RequestFactory()
        request = getattr(factory, method)(url, **headers)

        return self._do_request(request)

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
        headers = self._get_headers(headers or {})

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

        return self._do_request(request)
