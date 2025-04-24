from django.urls import path

from strawberry.django.views import GraphQLView as BaseGraphQLView
from tests.views.schema import Query, get_schema


class GraphQLView(BaseGraphQLView):
    def get_root_value(self, request) -> Query:
        return Query()


urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=get_schema())),
]
