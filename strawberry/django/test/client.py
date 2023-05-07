from typing import Any, Dict, Optional

from strawberry.test import BaseGraphQLTestClient


class GraphQLTestClient(BaseGraphQLTestClient):
    def request(
        self,
        body: Dict[str, object],
        headers: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, object]] = None,
    ) -> Any:
        if files:
            return self._client.post(
                self.url, data=body, format="multipart", headers=headers
            )

        return self._client.post(
            self.url, data=body, content_type="application/json", headers=headers
        )
