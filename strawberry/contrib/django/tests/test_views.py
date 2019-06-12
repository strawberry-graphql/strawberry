from django.test.client import RequestFactory

from strawberry.contrib.django.views import GraphQLPlaygroundView


def test_playground_view():
    factory = RequestFactory()

    request = factory.get("/")

    response = GraphQLPlaygroundView.as_view()(request)
    body = response.content.decode()

    assert "GraphQL Playground" in body
    assert f'endpoint: "{request.get_full_path()}"' in body
