async def test_no_query(aiohttp_app_client):
    params = {"variables": '{"name": "James"}'}

    response = await aiohttp_app_client.get("/graphql", params=params)
    assert response.status == 400


async def test_get_with_query_params(aiohttp_app_client):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    response = await aiohttp_app_client.get("/graphql", params=query)
    data = await response.json()
    assert response.status == 200
    assert data["data"]["hello"] == "Hello world"


async def test_can_pass_variables_with_query_params(aiohttp_app_client):
    query = {
        "query": "query Hello($name: String!) { hello(name: $name) }",
        "variables": '{"name": "James"}',
    }

    response = await aiohttp_app_client.get("/graphql", params=query)
    data = await response.json()
    assert response.status == 200
    assert data["data"]["hello"] == "Hello James"


async def test_post_fails_with_query_params(aiohttp_app_client):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    response = await aiohttp_app_client.post("/graphql", params=query)

    assert response.status == 400


async def test_does_not_allow_mutation(aiohttp_app_client):
    query = {
        "query": """
            mutation {
                hello
            }
        """
    }

    response = await aiohttp_app_client.get("/graphql", params=query)
    assert response.status == 400

    data = await response.text()
    assert data == "400: mutations are not allowed when using GET"


async def test_fails_if_allow_queries_via_get_false(aiohttp_app_client_no_get):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    response = await aiohttp_app_client_no_get.get("/graphql", params=query)
    assert response.status == 400
    data = await response.text()
    assert data == "400: queries are not allowed when using GET"
