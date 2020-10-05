import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import RequestFactory

import strawberry
from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.file_uploads import Upload


@strawberry.type
class Query:
    hello: str = "strawberry"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return text_file.read().decode()


schema = strawberry.Schema(query=Query, mutation=Mutation)


class GraphQLView(BaseGraphQLView):
    def get_root_value(self, request):
        return Query()


def test_upload():
    f = SimpleUploadedFile("file.txt", b"strawberry")

    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    factory = RequestFactory()

    request = factory.post(
        "/graphql/",
        data={
            "operations": json.dumps({"query": query, "variables": {"textFile": None}}),
            "map": json.dumps({"textFile": ["variables.textFile"]}),
            "textFile": f,
        },
        format="multipart",
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert not data.get("errors")
    assert data["data"]["readText"] == "strawberry"
