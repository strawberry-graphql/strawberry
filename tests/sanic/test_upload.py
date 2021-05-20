OPERATIONS_FIELD = (
    "------sanic\r\n"
    'Content-Disposition: form-data; name="operations"\r\n'
    "\r\n"
    "{"
    '"query": "mutation($textFile: Upload!){readText(textFile: $textFile)}",'
    '"variables": {"textFile": null}'
    "}\r\n"
)

MAP_FIELD = (
    "------sanic\r\n"
    'Content-Disposition: form-data; name="map"\r\n'
    "\r\n"
    '{"textFile": ["variables.textFile"]}\r\n'
)

TEXT_FILE_FIELD = (
    "------sanic\r\n"
    'Content-Disposition: form-data; name="textFile"; filename="textFile.txt"\r\n'
    "Content-Type: text/plain\r\n"
    "\r\n"
    "strawberry\r\n"
)

END = "------sanic--"


def test_single_file_upload(sanic_client):
    data = OPERATIONS_FIELD + MAP_FIELD + TEXT_FILE_FIELD + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        data=data,
        headers=headers,
    )

    assert response.status_code == 200
    assert not response.json.get("errors")
    assert response.json["data"]["readText"] == "strawberry"


def test_extra_form_data_fields_are_ignored(sanic_client):
    extra_field = (
        "------sanic\r\n"
        'Content-Disposition: form-data; name="extra_field"\r\n'
        "\r\n"
        "{}\r\n"
    )

    data = OPERATIONS_FIELD + MAP_FIELD + TEXT_FILE_FIELD + extra_field + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        data=data,
        headers=headers,
    )

    assert response.status_code == 200
    assert not response.json.get("errors")


def test_sending_invalid_form_data(sanic_client):
    headers = {"content-type": "multipart/form-data; boundary=----fake"}
    request, response = sanic_client.test_client.post(
        "/graphql",
        headers=headers,
    )

    assert response.status_code == 400
    assert "No GraphQL query found in the request" in response.text


def test_malformed_query(sanic_client):
    operations_field = (
        "------sanic\r\n"
        'Content-Disposition: form-data; name="operations"\r\n'
        "\r\n"
        "{"
        '"NOT_QUERY": "",'
        '"variables": {"textFile": null}'
        "}\r\n"
    )

    data = operations_field + MAP_FIELD + TEXT_FILE_FIELD + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        data=data,
        headers=headers,
    )

    assert response.status_code == 400
    assert "No GraphQL query found in the request" in response.text


def test_sending_invalid_json_body(sanic_client):
    operations_field = (
        "------sanic\r\n"
        'Content-Disposition: form-data; name="operations"\r\n'
        "\r\n"
        "}\r\n"
    )

    data = operations_field + MAP_FIELD + TEXT_FILE_FIELD + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        data=data,
        headers=headers,
    )

    assert response.status_code == 400
    assert "Unable to parse request body as JSON" in response.text


def test_upload_with_missing_file(sanic_client):
    data = OPERATIONS_FIELD + MAP_FIELD + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        data=data,
        headers=headers,
    )

    assert response.status_code == 400
    assert "File(s) missing in form data" in response.text
