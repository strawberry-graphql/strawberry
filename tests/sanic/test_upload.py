def test_single_file_upload(sanic_client):
    post_data = (
        "------sanic\r\n"
        'Content-Disposition: form-data; name="operations"\r\n'
        "\r\n"
        "{"
        '"query": "mutation($textFile: Upload!){readText(textFile: $textFile)}",'
        '"variables": {"textFile": null}'
        "}\r\n"
        "------sanic\r\n"
        'Content-Disposition: form-data; name="map"\r\n'
        "\r\n"
        '{"textFile": ["variables.textFile"]}\r\n'
        "------sanic\r\n"
        'Content-Disposition: form-data; name="textFile"; filename="textFile.txt"\r\n'
        "Content-Type: text/plain\r\n"
        "\r\n"
        "strawberry\r\n"
        "------sanic--"
    )

    request, response = sanic_client.test_client.post(
        "/graphql",
        data=post_data,
        headers={"content-type": "multipart/form-data; boundary=----sanic"},
    )

    assert response.status_code == 200

    data = response.json

    assert not data.get("errors")
    assert data["data"]["readText"] == "strawberry"
