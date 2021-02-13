import json
from io import BytesIO

import pytest

from .app import create_app


@pytest.fixture
def flask_client():
    app = create_app()

    with app.test_client() as client:
        yield client


def test_graphql_query(flask_client):
    f = (BytesIO(b"strawberry"), "textFile.txt")

    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    response = flask_client.post(
        "/graphql",
        data={
            "operations": json.dumps({"query": query, "variables": {"textFile": None}}),
            "map": json.dumps({"textFile": ["variables.textFile"]}),
            "textFile": f,
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    data = json.loads(response.data.decode())

    assert not data.get("errors")
    assert data["data"]["readText"] == "strawberry"
