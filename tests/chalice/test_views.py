import json
from http import HTTPStatus

import pytest

from chalice.test import Client, HTTPResponse

from .app import app


def test_chalice_server_index_route_returns():
    with Client(app) as client:
        response = client.http.get("/")
        assert response.status_code == HTTPStatus.OK
        assert response.json_body == {"strawberry": "cake"}


@pytest.mark.parametrize("header_value", ["text/html", "*/*"])
def test_graphiql_view_is_returned_if_accept_is_html_or_accept_all(header_value):
    with Client(app) as client:
        headers = {"Accept": header_value}
        response = client.http.get("/graphql", headers=headers)
        assert response.status_code == HTTPStatus.OK
        assert "GraphiQL" in str(response.body)


def test_graphiql_view_is_not_returned_if_accept_headers_is_none():
    with Client(app) as client:
        response = client.http.get("/graphql", headers=None)
        assert response.status_code == HTTPStatus.OK
        assert response_is_of_error_type(response)


def response_is_of_error_type(response: HTTPResponse) -> bool:
    if "errors" in response.json_body.keys():
        if response.status_code == HTTPStatus.OK:
            return True
    return False


def test_get_graphql_view_with_json_accept_type_is_rejected():
    with Client(app) as client:
        headers = {"Accept": "application/json"}
        response = client.http.get("/graphql", headers=headers)
        assert response.status_code == HTTPStatus.OK
        assert response_is_of_error_type(response)


def test_malformed_unparsable_json_query_returns_error():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # The query key in the json dict is missing
        query = "I am a malformed query"
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))
        assert response_is_of_error_type(response)


# These tests are checking that graphql is getting routed through the endpoint
# correctly to the strawberry execute_sync command, so just test one happy path case of a
# query and a mutation
def test_graphiql_query():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        query = {"query": "query GreetMe {greetings}"}
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))
        assert response.status_code == HTTPStatus.OK
        assert not response_is_of_error_type(response)
        assert "hello" == response.json_body["data"]["greetings"]


def test_graphiql_mutation():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        query = {"query": """mutation EchoMutation { echo(stringToEcho: "mark")} """}
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))
        assert response.status_code == HTTPStatus.OK
        assert "mark" == response.json_body["data"]["echo"]


def test_graphiql_query_with_malformed_json_gives_http_ok_and_bad_request_message():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        response = client.http.post("/graphql", headers=headers, body="{invalidjson")
        assert response.status_code == HTTPStatus.OK
        assert response_is_of_error_type(response)


def test_graphiql_query_with_no_request_body():
    with Client(app) as client:
        headers = {"Accept": "application/json"}
        response = client.http.post("/graphql", headers=headers, body="")
        assert response.status_code == HTTPStatus.OK
        assert response_is_of_error_type(response)
