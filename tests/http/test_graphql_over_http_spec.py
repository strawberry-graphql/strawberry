# ruff: noqa: N802
import pytest

from tests.http.clients.chalice import ChaliceHttpClient
from tests.http.clients.django import DjangoHttpClient
from tests.http.clients.sanic import SanicHttpClient


@pytest.mark.xfail(
    reason="Our integrations currently only return application/json",
    raises=AssertionError,
)
async def test_22EB(http_client):
    """
    SHOULD accept application/graphql-response+json and match the content-type
    """
    if isinstance(http_client, ChaliceHttpClient):
        pytest.xfail("The Chalice test client does not return any response headers")

    response = await http_client.query(
        method="post",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        query="{ __typename }",
    )
    assert response.status_code == 200
    assert "application/graphql-response+json" in response.headers["content-type"]


async def test_4655(http_client):
    """
    MUST accept application/json and match the content-type
    """
    if isinstance(http_client, ChaliceHttpClient):
        pytest.xfail("The Chalice test client does not return any response headers")

    response = await http_client.query(
        method="post",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        query="{ __typename }",
    )
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


async def test_47DE(http_client):
    """
    SHOULD accept */* and use application/json for the content-type
    """
    if isinstance(http_client, ChaliceHttpClient):
        pytest.xfail("The Chalice test client does not return any response headers")

    response = await http_client.query(
        method="post",
        headers={
            "Content-Type": "application/json",
            "Accept": "*/*",
        },
        query="{ __typename }",
    )
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


async def test_80D8(http_client):
    """
    SHOULD assume application/json content-type when accept is missing
    """
    if isinstance(http_client, ChaliceHttpClient):
        pytest.xfail("The Chalice test client does not return any response headers")

    response = await http_client.query(
        method="post",
        headers={"Content-Type": "application/json"},
        query="{ __typename }",
    )
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


async def test_82A3(http_client):
    """
    MUST use utf-8 encoding when responding
    """
    response = await http_client.query(
        method="post",
        headers={"Content-Type": "application/json"},
        query="{ __typename }",
    )
    assert response.status_code == 200
    assert isinstance(response.data, bytes)

    try:
        response.data.decode(encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        pytest.fail("Response body is not UTF-8 encoded")


async def test_BF61(http_client):
    """
    MUST accept utf-8 encoded request
    """
    response = await http_client.query(
        method="post",
        headers={"Content-Type": "application/json; charset=utf-8"},
        query='{ __type(name: "Run🏃Swim🏊") { name } }',
    )
    assert response.status_code == 200


async def test_78D5(http_client):
    """
    MUST assume utf-8 in request if encoding is unspecified
    """
    response = await http_client.query(
        method="post",
        headers={"Content-Type": "application/json"},
        query="{ __typename }",
    )
    assert response.status_code == 200


async def test_2C94(http_client):
    """
    MUST accept POST requests
    """
    response = await http_client.query(
        method="post",
        headers={"Content-Type": "application/json"},
        query="{ __typename }",
    )
    assert response.status_code == 200


async def test_5A70(http_client):
    """
    MAY accept application/x-www-form-urlencoded formatted GET requests
    """
    response = await http_client.query(method="get", query="{ __typename }")
    assert response.status_code == 200


async def test_9C48(http_client):
    """
    MAY NOT allow executing mutations on GET requests
    """
    response = await http_client.query(
        method="get",
        headers={"Accept": "application/graphql-response+json"},
        query="mutation { __typename }",
    )
    assert 400 <= response.status_code <= 499


@pytest.mark.xfail(
    reason="OPTIONAL - currently supported by Channels, Chalice, and Sanic",
    raises=AssertionError,
)
async def test_9ABE(http_client):
    """
    MAY respond with 4xx status code if content-type is not supplied on POST requests
    """
    if isinstance(http_client, DjangoHttpClient):
        pytest.xfail("Our Django test client defaults to multipart/form-data")

    response = await http_client.post(
        url="/graphql",
        headers={},
        json={"query": "{ __typename }"},
    )
    assert 400 <= response.status_code <= 499


async def test_03D4(http_client):
    """
    MUST accept application/json POST requests
    """
    response = await http_client.query(
        method="post",
        headers={"Content-Type": "application/json"},
        query="{ __typename }",
    )
    assert response.status_code == 200


async def test_A5BF(http_client):
    """
    MAY use 400 status code when request body is missing on POST
    """
    if isinstance(http_client, (DjangoHttpClient, ChaliceHttpClient, SanicHttpClient)):
        pytest.xfail(
            "Our Django, Chalice, and Sanic test clients currently require a body"
        )

    response = await http_client.post(
        url="/graphql",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


async def test_423L(http_client):
    """
    MAY use 400 status code on missing {query} parameter
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={"notquery": "{ __typename }"},
    )
    assert response.status_code == 400


@pytest.mark.xfail(
    reason="OPTIONAL - Currently results in lots of TypeErrors",
    raises=AssertionError,
)
@pytest.mark.parametrize(
    "invalid",
    [{"obj": "ect"}, 0, False, ["array"]],
    ids=["LKJ0", "LKJ1", "LKJ2", "LKJ3"],
)
async def test_LKJx(http_client, invalid):
    """
    MAY use 400 status code on invalid {query} parameter
    """
    response = await http_client.post(
        url="/graphql",
        headers={"Content-Type": "application/json"},
        json={"query": invalid},
    )
    assert response.status_code == 400


async def test_34A2(http_client):
    """
    SHOULD allow string {query} parameter when accepting application/graphql-response+json
    """
    response = await http_client.query(
        method="post",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        query="{ __typename }",
    )
    assert response.status_code == 200


async def test_13EE(http_client):
    """
    MUST allow string {query} parameter when accepting application/json
    """
    response = await http_client.query(
        method="post",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        query="{ __typename }",
    )
    assert response.status_code == 200
    assert isinstance(response.json, dict)
    assert "errors" not in response.json


@pytest.mark.xfail(
    reason="OPTIONAL - Currently results in lots of CannotGetOperationTypeErrors",
    raises=AssertionError,
)
@pytest.mark.parametrize(
    "invalid",
    [{"obj": "ect"}, 0, False, ["array"]],
    ids=["6C00", "6C01", "6C02", "6C03"],
)
async def test_6C0x(http_client, invalid):
    """
    MAY use 400 status code on invalid {operationName} parameter
    """
    response = await http_client.post(
        url="/graphql",
        headers={"Content-Type": "application/json"},
        json={
            "operationName": invalid,
            "query": "{ __typename }",
        },
    )
    assert response.status_code == 400


async def test_8161(http_client):
    """
    SHOULD allow string {operationName} parameter when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={
            "operationName": "Query",
            "query": "query Query { __typename }",
        },
    )
    assert response.status_code == 200


async def test_B8B3(http_client):
    """
    MUST allow string {operationName} parameter when accepting application/json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "operationName": "Query",
            "query": "query Query { __typename }",
        },
    )
    assert response.status_code == 200
    assert isinstance(response.json, dict)
    assert "errors" not in response.json


@pytest.mark.parametrize(
    "parameter",
    ["variables", "operationName", "extensions"],
    ids=["94B0", "94B1", "94B2"],
)
async def test_94Bx(http_client, parameter):
    """
    SHOULD allow null varibales/operationName/extensions parameter when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={
            "query": "{ __typename }",
            parameter: None,
        },
    )
    assert response.status_code == 200
    assert "errors" not in response.json


@pytest.mark.parametrize(
    "parameter",
    ["variables", "operationName", "extensions"],
    ids=["0220", "0221", "0222"],
)
async def test_022x(http_client, parameter):
    """
    MUST allow null variables/operationName/extensions parameter when accepting application/json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "query": "{ __typename }",
            parameter: None,
        },
    )
    assert response.status_code == 200
    assert "errors" not in response.json


@pytest.mark.xfail(
    reason="OPTIONAL - Currently results in lots of TypeErrors", raises=AssertionError
)
@pytest.mark.parametrize(
    "invalid",
    ["string", 0, False, ["array"]],
    ids=["4760", "4761", "4762", "4763"],
)
async def test_476x(http_client, invalid):
    """
    MAY use 400 status code on invalid {variables} parameter
    """
    response = await http_client.post(
        url="/graphql",
        headers={"Content-Type": "application/json"},
        json={
            "query": "{ __typename }",
            "variables": invalid,
        },
    )
    assert response.status_code == 400


async def test_2EA1(http_client):
    """
    SHOULD allow map {variables} parameter when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={
            "query": "query Type($name: String!) { __type(name: $name) { name } }",
            "variables": {"name": "sometype"},
        },
    )
    assert response.status_code == 200


async def test_28B9(http_client):
    """
    MUST allow map {variables} parameter when accepting application/json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "query": "query Type($name: String!) { __type(name: $name) { name } }",
            "variables": {"name": "sometype"},
        },
    )
    assert response.status_code == 200
    assert isinstance(response.json, dict)
    assert "errors" not in response.json


async def test_D6D5(http_client):
    """
    MAY allow URL-encoded JSON string {variables} parameter in GETs when accepting application/graphql-response+json
    """
    response = await http_client.query(
        query="query Type($name: String!) { __type(name: $name) { name } }",
        variables={"name": "sometype"},
        method="get",
        headers={"Accept": "application/graphql-response+json"},
    )
    assert response.status_code == 200


async def test_6A70(http_client):
    """
    MAY allow URL-encoded JSON string {variables} parameter in GETs when accepting application/json
    """
    response = await http_client.query(
        query="query Type($name: String!) { __type(name: $name) { name } }",
        variables={"name": "sometype"},
        method="get",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    assert isinstance(response.json, dict)
    assert "errors" not in response.json


@pytest.mark.xfail(
    reason="OPTIONAL - Currently not supported by Strawberry", raises=AssertionError
)
@pytest.mark.parametrize(
    "invalid",
    ["string", 0, False, ["array"]],
    ids=["58B0", "58B1", "58B2", "58B3"],
)
async def test_58Bx(http_client, invalid):
    """
    MAY use 400 status code on invalid {extensions} parameter
    """
    response = await http_client.post(
        url="/graphql",
        headers={"Content-Type": "application/json"},
        json={
            "query": "{ __typename }",
            "extensions": invalid,
        },
    )
    assert response.status_code == 400


async def test_428F(http_client):
    """
    SHOULD allow map {extensions} parameter when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={
            "query": "{ __typename }",
            "extensions": {"some": "value"},
        },
    )
    assert response.status_code == 200


async def test_1B7A(http_client):
    """
    MUST allow map {extensions} parameter when accepting application/json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "query": "{ __typename }",
            "extensions": {"some": "value"},
        },
    )
    assert response.status_code == 200
    assert isinstance(response.json, dict)
    assert "errors" not in response.json


async def test_B6DC(http_client):
    """
    MAY use 4xx or 5xx status codes on JSON parsing failure
    """
    response = await http_client.post(
        url="/graphql",
        headers={"Content-Type": "application/json"},
        data=b'{ "not a JSON',
    )
    assert 400 <= response.status_code <= 599


async def test_BCF8(http_client):
    """
    MAY use 400 status code on JSON parsing failure
    """
    response = await http_client.post(
        url="/graphql",
        headers={"Content-Type": "application/json"},
        data=b'{ "not a JSON',
    )
    assert response.status_code == 400


async def test_8764(http_client):
    """
    MAY use 4xx or 5xx status codes if parameters are invalid
    """
    response = await http_client.post(
        url="/graphql",
        headers={"Content-Type": "application/json"},
        json={"qeury": "{ __typename }"},  # typo in 'query'
    )
    assert 400 <= response.status_code <= 599


async def test_3E3A(http_client):
    """
    MAY use 400 status code if parameters are invalid
    """
    response = await http_client.post(
        url="/graphql",
        headers={"Content-Type": "application/json"},
        json={"qeury": "{ __typename }"},  # typo in 'query'
    )
    assert response.status_code == 400


async def test_39AA(http_client):
    """
    MUST accept a map for the {extensions} parameter
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "query": "{ __typename }",
            "extensions": {"some": "value"},
        },
    )
    assert response.status_code == 200
    assert isinstance(response.json, dict)
    assert "errors" not in response.json


async def test_572B(http_client):
    """
    SHOULD use 200 status code on document parsing failure when accepting application/json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={"query": "{"},
    )
    assert response.status_code == 200


async def test_DFE2(http_client):
    """
    SHOULD use 200 status code on document validation failure when accepting application/json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "query": "{ 8f31403dfe404bccbb0e835f2629c6a7 }"
        },  # making sure the field doesn't exist
    )
    assert response.status_code == 200


async def test_7B9B(http_client):
    """
    SHOULD use a status code of 200 on variable coercion failure when accepting application/json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "query": "query CoerceFailure($id: ID!){ __typename }",
            "variables": {"id": None},
        },
    )
    assert response.status_code == 200


@pytest.mark.xfail(
    reason="Currently results in status 200 with GraphQL errors", raises=AssertionError
)
async def test_865D(http_client):
    """
    SHOULD use 4xx or 5xx status codes on document parsing failure when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={"query": "{"},
    )
    assert 400 <= response.status_code <= 599


@pytest.mark.xfail(
    reason="Currently results in status 200 with GraphQL errors", raises=AssertionError
)
async def test_556A(http_client):
    """
    SHOULD use 400 status code on document parsing failure when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={"query": "{"},
    )
    assert response.status_code == 400


@pytest.mark.xfail(
    reason="Currently results in status 200 with GraphQL errors", raises=AssertionError
)
async def test_D586(http_client):
    """
    SHOULD NOT contain the data entry on document parsing failure when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={"query": "{"},
    )
    assert response.status_code == 400
    assert "data" not in response.json


@pytest.mark.xfail(
    reason="Currently results in status 200 with GraphQL errors", raises=AssertionError
)
async def test_51FE(http_client):
    """
    SHOULD use 4xx or 5xx status codes on document validation failure when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={
            "query": "{ 8f31403dfe404bccbb0e835f2629c6a7 }",  # making sure the field doesn't exist
        },
    )
    assert 400 <= response.status_code <= 599


@pytest.mark.xfail(
    reason="Currently results in status 200 with GraphQL errors", raises=AssertionError
)
async def test_74FF(http_client):
    """
    SHOULD use 400 status code on document validation failure when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={
            "query": "{ 8f31403dfe404bccbb0e835f2629c6a7 }",  # making sure the field doesn't exist
        },
    )
    assert response.status_code == 400


@pytest.mark.xfail(
    reason="Currently results in status 200 with GraphQL errors", raises=AssertionError
)
async def test_5E5B(http_client):
    """
    SHOULD NOT contain the data entry on document validation failure when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={
            "query": "{ 8f31403dfe404bccbb0e835f2629c6a7 }",  # making sure the field doesn't exist
        },
    )
    assert response.status_code == 400
    assert "data" not in response.json


@pytest.mark.xfail(
    reason="Currently results in status 200 with GraphQL errors", raises=AssertionError
)
async def test_86EE(http_client):
    """
    SHOULD use a status code of 400 on variable coercion failure when accepting application/graphql-response+json
    """
    response = await http_client.post(
        url="/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/graphql-response+json",
        },
        json={
            "query": "query CoerceFailure($id: ID!){ __typename }",
            "variables": {"id": None},
        },
    )
    assert response.status_code == 400
