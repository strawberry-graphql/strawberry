from typing import Any, Dict, Optional

from strawberry.test import BaseGraphQLTestClient, Body, Response


class GraphQLTestClient(BaseGraphQLTestClient):
    def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        asserts_errors: Optional[bool] = True,
    ) -> Response:
        body: Body = {"query": query}

        if variables:
            body["variables"] = variables

        resp = self._client.post(
            "/graphql/", data=body, content_type="application/json", headers=headers
        )
        data = resp.json()

        response = Response(
            errors=data.get("errors"),
            data=data.get("data"),
            extensions=data.get("extensions"),
        )
        if asserts_errors:
            assert response.errors is None

        return response

    def force_login(self, user):
        self._client.force_login(user)
