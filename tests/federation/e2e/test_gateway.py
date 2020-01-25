import pytest

import httpx


@pytest.mark.skip(reason="Work in progress")
def test_gateway_works():
    query = """{
        topProducts {
            name
            upc
            reviews {
                body
            }
        }
    }"""

    response = httpx.post("http://localhost:4000/", data={"query": query})

    assert response.json() == {}
