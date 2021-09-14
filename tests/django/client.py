from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, TypedDict


@dataclass
class Response:
    errors: Optional[Dict[str, Any]]
    data: Optional[Dict[str, Any]]


class Body(TypedDict, total=False):
    query: str
    variables: Optional[Dict[str, Any]]


class BaseGraphQLTestClient:
    def __init__(self, client):
        self._client = client

    @abstractmethod
    def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> Response:
        raise NotImplementedError

    def force_login(self, user):
        raise NotImplementedError


class GraphQLTestClient(BaseGraphQLTestClient):
    def query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Response:
        body: Body = {"query": query}

        if variables:
            body["variables"] = variables

        resp = self._client.post(
            "/graphql/",
            data=body,
            content_type="application/json",
        )
        data = resp.json()
        return Response(errors=data.get("errors"), data=data.get("data"))

    def force_login(self, user):
        self._client.force_login(user)
