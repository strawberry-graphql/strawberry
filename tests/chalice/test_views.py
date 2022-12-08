import json

import pytest
from werkzeug.urls import url_encode, url_unparse

from chalice import Chalice  # type: ignore
from chalice.test import Client
from strawberry.chalice.views import GraphQLView

from .app import app


def test_chalice_server_index_route_returns():
    with Client(app) as client:
        response = client.http.get("/")
        assert response.status_code == 200
        assert response.json_body == {"strawberry": "cake"}


@pytest.mark.parametrize("header_value", ["text/html", "*/*"])
def test_graphiql_view_is_returned_if_accept_is_html_or_accept_all(header_value):
    with Client(app) as client:
        headers = {"Accept": header_value}
        response = client.http.get("/graphql", headers=headers)

        assert response.status_code == 200
        assert "GraphiQL" in str(response.body)


def test_graphiql_view_is_not_returned_if_accept_headers_is_none():
    with Client(app) as client:
        response = client.http.get("/graphql", headers=None)

        assert response.status_code == 404


def test_get_graphql_view_with_json_accept_type_is_rejected():
    with Client(app) as client:
        headers = {"Accept": "application/json"}
        response = client.http.get("/graphql", headers=headers)

        assert response.status_code == 404


def test_malformed_unparsable_json_query_returns_error():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # The query key in the json dict is missing
        query = "I am a malformed query"
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))

        assert response.status_code == 400


def test_malformed_unparsable_json_query_returns_error_via_get():
    with Client(app) as client:
        response = client.http.get("/graphql?query={ hello }&variables='{'")

        assert response.status_code == 400


# These tests are checking that graphql is getting routed through the endpoint
# correctly to the strawberry execute_sync command
def test_query():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        query = {"query": "query GreetMe {greetings}"}
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))

        assert response.status_code == 200
        assert response.json_body["data"]["greetings"] == "hello"


def test_query_via_get():
    with Client(app) as client:
        response = client.http.get("/graphql?query={greetings}")

        assert response.status_code == 200
        assert response.json_body["data"]["greetings"] == "hello"


def test_query_via_get_when_disabled():
    with Client(app) as client:
        response = client.http.get("/graphql-no-get?query={greetings}")

        assert response.status_code == 400
        assert response.json_body == {
            "Code": "BadRequestError",
            "Message": "queries are not allowed when using GET",
        }


def test_can_pass_variables():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        query = {
            "query": "query Hello($name: String!) { hello(name: $name) }",
            "variables": {"name": "James"},
        }
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))

        assert response.status_code == 200
        assert response.json_body["data"]["hello"] == "Hello James"


def test_mutation():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        query = {"query": """mutation EchoMutation { echo(stringToEcho: "mark")} """}
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))

        assert response.status_code == 200
        assert "mark" == response.json_body["data"]["echo"]


def test_query_with_malformed_json_returns_bad_request():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        response = client.http.post("/graphql", headers=headers, body="{invalidjson")

        assert response.status_code == 400


def test_query_with_no_request_body():
    with Client(app) as client:
        headers = {"Accept": "application/json"}
        response = client.http.post("/graphql", headers=headers, body="")

        assert response.status_code == 404


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


def test_query_unsupported_method():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        query = {"query": "query GreetMe {greetings}"}
        response = client.http.put(
            "/graphql-no-graphiql", headers=headers, body=json.dumps(query)
        )

        assert response.status_code == 405
        assert (
            response.json_body["Message"]
            == "Unsupported method, must be of request type POST or GET"
        )


@pytest.mark.parametrize("header_value", ["text/html", "*/*"])
def test_no_graphiql_view_is_returned_if_false(header_value):
    with Client(app) as client:
        headers = {"Accept": header_value}
        response = client.http.get("/graphql-no-graphiql", headers=headers)

        assert response.status_code == 404


def test_query_custom_status_code():
    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        query = {"query": "query { teapot }"}
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))

        assert response.status_code == 418
        assert response.json_body["data"]["teapot"] == "🫖"


def test_passing_render_graphiql_is_deprecated():
    from .app import schema

    with pytest.warns(DeprecationWarning):
        GraphQLView(schema=schema, render_graphiql=True)


def test_custom_encode_json():
    from .app import schema

    class CustomGraphQLView(GraphQLView):
        def encode_json(self, data):
            return '"custom"'

    view = CustomGraphQLView(schema=schema)

    app = Chalice(app_name="test_encode_json")

    @app.route("/graphql", methods=["GET", "POST"], content_types=["application/json"])
    def handle_graphql():
        return view.execute_request(app.current_request)

    with Client(app) as client:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        query = {"query": "query GreetMe {greetings}"}
        response = client.http.post("/graphql", headers=headers, body=json.dumps(query))

        assert response.status_code == 200
        assert response.json_body == "custom"
