from __future__ import annotations

from typing import Dict, Optional

from typing_extensions import Literal

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

    async def _request(
        self,
        method: Literal["get", "post"],
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        headers = (
            {
                f"HTTP_{key.upper().replace('-', '_')}": value
                for key, value in headers.items()
            }
            if headers
            else {}
        )
        additional_arguments = {**kwargs, **headers}

        factory = RequestFactory()
        request = getattr(factory, method)(url, **additional_arguments)

        try:
            response = GraphQLView.as_view(schema=schema, graphiql=self.graphiql)(
                request
            )
        except Http404:
            return Response(status_code=404, data=b"Not found")
        else:
            return Response(status_code=response.status_code, data=response.content)

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Response:
        return await self._request("get", url, headers=headers)

    async def post(
        self, url: str, json: JSON, headers: Optional[Dict[str, str]] = None
    ) -> Response:
        return await self._request(
            "post", url, data=json, content_type="application/json", headers=headers
        )
