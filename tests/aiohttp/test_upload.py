import json
from io import BytesIO

import aiohttp


async def test_upload(aiohttp_app_client):
    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    f = BytesIO(b"strawberry")
    operations = json.dumps({"query": query, "variables": {"textFile": None}})
    file_map = json.dumps({"textFile": ["variables.textFile"]})

    form_data = aiohttp.FormData()
    form_data.add_field("textFile", f, filename="textFile.txt")
    form_data.add_field("operations", operations)
    form_data.add_field("map", file_map)

    response = await aiohttp_app_client.post("/graphql", data=form_data)
    assert response.status == 200

    data = await response.json()

    assert not data.get("errors")
    assert data["data"]["readText"] == "strawberry"


async def test_extra_form_data_fields_are_ignored(aiohttp_app_client):
    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    f = BytesIO(b"strawberry")
    operations = json.dumps({"query": query, "variables": {"textFile": None}})
    file_map = json.dumps({"textFile": ["variables.textFile"]})
    extra_field_data = json.dumps({})

    form_data = aiohttp.FormData()
    form_data.add_field("textFile", f, filename="textFile.txt")
    form_data.add_field("operations", operations)
    form_data.add_field("map", file_map)
    form_data.add_field("extra_field", extra_field_data)

    response = await aiohttp_app_client.post("/graphql", data=form_data)
    assert response.status == 200


async def test_sending_invalid_form_data(aiohttp_app_client):
    headers = {"content-type": "multipart/form-data; boundary=----fake"}
    response = await aiohttp_app_client.post("/graphql", headers=headers)
    reason = await response.text()

    assert response.status == 400
    assert reason == "400: Unable to parse the multipart body"
