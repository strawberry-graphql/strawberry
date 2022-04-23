from __future__ import annotations

from django.test.client import RequestFactory

from strawberry.django.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    def get_root_value(self, request):
        return Query()


class DjangoHttpClient(HttpClient):
    async def post(self, url: str, json: JSON) -> Response:
        factory = RequestFactory()

        request = factory.post(url, json, content_type="application/json")
        response = GraphQLView.as_view(schema=schema)(request)

        return Response(status_code=response.status_code, data=response.content)
