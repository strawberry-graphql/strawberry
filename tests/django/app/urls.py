from django.urls import path

from strawberry.django.views import GraphQLView as BaseGraphQLView

from .schema import Query, schema


class GraphQLView(BaseGraphQLView):
    def get_root_value(self, request):
        return Query()


urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema)),
]
