from __future__ import annotations

import json
from io import BytesIO
from typing import Dict, Optional, Union

from typing_extensions import Literal

from django.core.exceptions import BadRequest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http.response import Http404
from django.test.client import RequestFactory

from strawberry.django.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import HttpClient, Response


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

    async def _request(
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
            data = body if files else json.dumps(body)

        factory = RequestFactory()
        request = getattr(factory, method)(
            "/graphql",
            data=data,
            **additional_arguments,
        )

        try:
            response = GraphQLView.as_view(schema=schema, graphiql=self.graphiql)(
                request
            )
        except Http404:
            return Response(status_code=404, data=b"Not found")
        except BadRequest as e:
            return Response(status_code=400, data=e.args[0].encode())
        else:
            return Response(status_code=response.status_code, data=response.content)
