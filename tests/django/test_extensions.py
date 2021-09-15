import json

from django.test.client import RequestFactory

import strawberry
from strawberry.django.views import GraphQLView
from strawberry.extensions import Extension


class MyExtension(Extension):
    def get_results(self):
        return {"example": "example"}


@strawberry.type
class Query:
    hello: str = "strawberry"


schema = strawberry.Schema(query=Query, extensions=[MyExtension])


def test_extensions():
    query = "{ hello }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert response["content-type"] == "application/json"
    assert data["extensions"]["example"] == "example"
