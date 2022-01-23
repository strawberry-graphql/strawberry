async def test_no_graphiql_no_query(aiohttp_app_client):
    params = {
        "variables": """
            query {
                hello
            }
        """
    }

    response = await aiohttp_app_client.get("/graphql", params=params)
    assert response.status == 400


async def test_no_graphiql_get_with_query_params(aiohttp_app_client):
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
    assert data["data"]["hello"] == "strawberry"


async def test_post_with_query_params(aiohttp_app_client):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    response = await aiohttp_app_client.post("/graphql", params=query)
    data = await response.json()
    assert response.status == 200
    assert data["data"]["hello"] == "strawberry"
