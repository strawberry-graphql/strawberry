from typing import Any, Dict, Optional

from strawberry.test import BaseGraphQLTestClient, Body, Response


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
