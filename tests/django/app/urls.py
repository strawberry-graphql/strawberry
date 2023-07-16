from typing import Any

from django.http import HttpRequest
from django.urls import path

from strawberry.django.views import GraphQLView as BaseGraphQLView
from tests.http.schema import Query, get_schema


class GraphQLView(BaseGraphQLView[object, Any]):
    def get_root_value(self, request: HttpRequest) -> Query:
        return Query()


urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=get_schema())),
]
