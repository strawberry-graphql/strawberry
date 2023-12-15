from .clients.base import HttpClient

__QUERY = """{
  __typename
}"""

# see https://www.apollographql.com/docs/apollo-server/performance/apq/
async def test_apq_initial_request_do_nothing(http_client: HttpClient):
    method = "GET"

    response = await http_client.query(query="{ hello  }", extensions={
        "persistedQuery": 1
    })
    json = response.json
    assert json["data"]["hello"] == "Hello world"

async def test_apq_no_query(http_client: HttpClient):
  method = "GET"

  response = await http_client.query(query=None, extensions={
      "persistedQuery": 1
  })
  json = response.json
  assert json["data"]["hello"] == "Hello world"
