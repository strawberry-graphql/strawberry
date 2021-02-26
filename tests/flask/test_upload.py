import json
from io import BytesIO


def test_upload(flask_client):
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
