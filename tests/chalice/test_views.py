import json
from http import HTTPStatus

from chalice.test import Client, HTTPResponse

from .app import app


def test_chalice_server_index_route_returns():
    with Client(app) as client:
        response = client.http.get("/")
        assert response.status_code == 200
        assert response.json_body == {"strawberry": "cake"}


def test_graphiql_view_is_returned_if_accept_is_html():
    with Client(app) as client:
        headers = {"Accept": "text/html"}
        response = client.http.get("/graphql", headers=headers)
        assert response.status_code == 200
        assert "GraphiQL" in str(response.body)


def response_is_of_error_type(response: HTTPResponse):
    if "errors" in response.json_body.keys():
        if response.status_code == HTTPStatus.OK:
            return True
    return False


def test_get_graphql_view_with_json_accept_type_is_rejected():
    with Client(app) as client:
        headers = {"Accept": "application/json"}
        response = client.http.get("/graphql", headers=headers)
        assert response_is_of_error_type(response)


def test_malformed_unparsable_json_query_returns_error():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # The query key in the json dict is missing
        query = "I am a malformed query"
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))
        assert response_is_of_error_type(response)


# Tests from this points are checking that graphql is getting routed through the endpoint
# correctly to the strawberry execute_sync command, so just test one happy path case of a
# query and a mutation as execute_sync command is tested elsewhere.
def test_graphiql_query():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        query = {"query": "query GreetMe {greetings}"}
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))
        assert response.status_code == HTTPStatus.OK
        assert "hello" == response.json_body["data"]["greetings"]


def test_graphiql_mutation():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        query = {"query": """ mutation EchoMutation { echo(stringToEcho: "mark")} """}
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))
        assert response.status_code == HTTPStatus.OK
        assert "mark" == response.json_body["data"]["echo"]
