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

MULTI_UPLOAD_OPERATIONS_FIELD = (
    "------sanic\r\n"
    'Content-Disposition: form-data; name="operations"\r\n'
    "\r\n"
    "{"
    '"query": "mutation($files: [Upload!]!){readFiles(files: $files)}",'
    '"variables": {"files": [null, null]}'
    "}\r\n"
)

MULTI_UPLOAD_MAP_FIELD = (
    "------sanic\r\n"
    'Content-Disposition: form-data; name="map"\r\n'
    "\r\n"
    '{"file1": ["variables.files.0"], "file2": ["variables.files.1"]}\r\n'
)

MULTI_UPLOAD_TEXT_FILE1_FIELD = (
    "------sanic\r\n"
    'Content-Disposition: form-data; name="file1"; filename="file1.txt"\r\n'
    "Content-Type: text/plain\r\n"
    "\r\n"
    "strawberry1\r\n"
)

MULTI_UPLOAD_TEXT_FILE2_FIELD = (
    "------sanic\r\n"
    'Content-Disposition: form-data; name="file2"; filename="file2.txt"\r\n'
    "Content-Type: text/plain\r\n"
    "\r\n"
    "strawberry2\r\n"
)

COMPLEX_UPLOAD_OPERATIONS_FIELD = (
    "------sanic\r\n"
    'Content-Disposition: form-data; name="operations"\r\n'
    "\r\n"
    "{"
    '"query": "mutation($folder: FolderInput!){readFolder(folder: $folder)}",'
    '"variables": {"folder": {"files": [null, null]}}'
    "}\r\n"
)

COMPLEX_UPLOAD_MAP_FIELD = (
    "------sanic\r\n"
    'Content-Disposition: form-data; name="map"\r\n'
    "\r\n"
    '{"file1": ["variables.folder.files.0"], "file2": ["variables.folder.files.1"]}\r\n'
)

END = "------sanic--"


def test_single_file_upload(sanic_client):
    content = OPERATIONS_FIELD + MAP_FIELD + TEXT_FILE_FIELD + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        content=content,
        headers=headers,
    )

    assert response.status_code == 200
    assert not response.json.get("errors")
    assert response.json["data"]["readText"] == "strawberry"


def test_file_list_upload(sanic_client):
    content = (
        MULTI_UPLOAD_OPERATIONS_FIELD
        + MULTI_UPLOAD_MAP_FIELD
        + MULTI_UPLOAD_TEXT_FILE1_FIELD
        + MULTI_UPLOAD_TEXT_FILE2_FIELD
        + END
    )
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        content=content,
        headers=headers,
    )

    assert response.status_code == 200
    assert not response.json.get("errors")

    assert len(response.json["data"]["readFiles"]) == 2
    assert response.json["data"]["readFiles"][0] == "strawberry1"
    assert response.json["data"]["readFiles"][1] == "strawberry2"


def test_nested_file_list(sanic_client):
    content = (
        COMPLEX_UPLOAD_OPERATIONS_FIELD
        + COMPLEX_UPLOAD_MAP_FIELD
        + MULTI_UPLOAD_TEXT_FILE1_FIELD
        + MULTI_UPLOAD_TEXT_FILE2_FIELD
        + END
    )
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        content=content,
        headers=headers,
    )

    assert response.status_code == 200
    assert not response.json.get("errors")

    assert len(response.json["data"]["readFolder"]) == 2
    assert response.json["data"]["readFolder"][0] == "strawberry1"
    assert response.json["data"]["readFolder"][1] == "strawberry2"


def test_extra_form_data_fields_are_ignored(sanic_client):
    extra_field = (
        "------sanic\r\n"
        'Content-Disposition: form-data; name="extra_field"\r\n'
        "\r\n"
        "{}\r\n"
    )

    content = OPERATIONS_FIELD + MAP_FIELD + TEXT_FILE_FIELD + extra_field + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        content=content,
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

    content = operations_field + MAP_FIELD + TEXT_FILE_FIELD + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        content=content,
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

    content = operations_field + MAP_FIELD + TEXT_FILE_FIELD + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        content=content,
        headers=headers,
    )

    assert response.status_code == 400
    assert "Unable to parse request body as JSON" in response.text


def test_upload_with_missing_file(sanic_client):
    content = OPERATIONS_FIELD + MAP_FIELD + END
    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = sanic_client.test_client.post(
        "/graphql",
        data=content,
        headers=headers,
    )

    assert response.status_code == 400
    assert "File(s) missing in form data" in response.text
