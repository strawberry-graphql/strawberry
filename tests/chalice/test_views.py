from werkzeug.urls import url_encode, url_unparse

from chalice.test import Client

from .app import app


def test_query_with_query_params():
    with Client(app) as client:
        params = {
            "query": """
                query GreetMe {
                    greetings
                }
            """
        }
        query_url = url_unparse(("", "", "/graphql", url_encode(params), ""))
        response = client.http.get(query_url)

        assert response.status_code == 200
        assert response.json_body["data"]["greetings"] == "hello"


def test_can_pass_variables_with_query_params():
    with Client(app) as client:
        params = {
            "query": "query Hello($name: String!) { hello(name: $name) }",
            "variables": '{"name": "James"}',
        }
        query_url = url_unparse(("", "", "/graphql", url_encode(params), ""))
        response = client.http.get(query_url)

        assert response.status_code == 200
        assert response.json_body["data"]["hello"] == "Hello James"


def test_query_with_missing_query():
    with Client(app) as client:
        params = {
            "abc": """
                query GreetMe {
                    greetings
                }
            """
        }
        query_url = url_unparse(("", "", "/graphql", url_encode(params), ""))
        response = client.http.get(query_url)

        assert response.status_code == 400
        assert response.json_body["Message"] == "No GraphQL query found in the request"
