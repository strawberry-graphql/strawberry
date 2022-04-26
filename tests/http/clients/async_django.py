from __future__ import annotations

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.http.response import Http404
from django.test.client import RequestFactory

from strawberry.django.views import AsyncGraphQLView as BaseAsyncGraphQLView

from ..schema import Query, schema
from . import Response
from .django import DjangoHttpClient


class AsyncGraphQLView(BaseAsyncGraphQLView):
    async def get_root_value(self, request):
        return Query()


class AsyncDjangoHttpClient(DjangoHttpClient):
    async def _do_request(self, request: RequestFactory) -> Response:
        try:
            response = await AsyncGraphQLView.as_view(
                schema=schema,
                graphiql=self.graphiql,
                allow_queries_via_get=self.allow_queries_via_get,
            )(request)
        except Http404:
            return Response(status_code=404, data=b"Not found")
        except (BadRequest, SuspiciousOperation) as e:
            return Response(status_code=400, data=e.args[0].encode())
        else:
            return Response(status_code=response.status_code, data=response.content)
