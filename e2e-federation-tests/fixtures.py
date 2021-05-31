from dataclasses import dataclass
from typing import Any, Dict, Optional

import pytest

import httpx


@dataclass
class Response:
    errors: Optional[Dict[str, Any]]
    data: Optional[Dict[str, Any]]


class GraphQLClient:
    def query(
        self,
        query: str,
        variables: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        body: Dict[str, Any] = {"query": query}
        headers = headers or {}

        if variables:
            body["variables"] = variables

        response = httpx.post(
            "http://localhost:7000/graphql", json=body, headers=headers
        )
        data = response.json()
        return Response(errors=data.get("errors"), data=data.get("data"))


@pytest.fixture
async def graphql_client():
    return GraphQLClient()
