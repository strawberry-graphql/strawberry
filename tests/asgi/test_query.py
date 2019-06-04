def test_simple_query(schema, test_client):
    response = test_client.post("/", json={"query": "{ hello }"})

    assert response.json() == {"data": {"hello": "Hello world"}}


def test_returns_errors(schema, test_client):
    response = test_client.post("/", json={"query": "{ donut }"})

    assert response.json() == {
        "data": None,
        "errors": [
            {
                "locations": [[1, 3]],
                "message": "Cannot query field 'donut' on type 'Query'.",
                "path": None,
            }
        ],
    }


def test_can_pass_variables(schema, test_client):
    response = test_client.post(
        "/",
        json={
            "query": "query Hello($name: String!) { hello(name: $name) }",
            "variables": {"name": "James"},
        },
    )

    assert response.json() == {"data": {"hello": "Hello James"}}
