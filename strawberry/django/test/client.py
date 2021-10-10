from typing import Any, Dict, Optional

from strawberry.test import BaseGraphQLTestClient


class GraphQLTestClient(BaseGraphQLTestClient):
    def request(
        self,
        body: Dict[str, Any],
        headers: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ):
        if files:
            return self._client.post(
                "/graphql/", data=body, format="multipart", headers=headers
            )

        return self._client.post(
            "/graphql/", data=body, content_type="application/json", headers=headers
        )
