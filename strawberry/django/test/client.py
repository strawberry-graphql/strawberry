from typing import Any

from strawberry.test import BaseGraphQLTestClient


class GraphQLTestClient(BaseGraphQLTestClient):
    def request(
        self,
        body: dict[str, object],
        headers: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
    ) -> Any:
        if files:
            return self._client.post(
                self.url, data=body, format="multipart", headers=headers
            )

        return self._client.post(
            self.url, data=body, content_type="application/json", headers=headers
        )


__all__ = ["GraphQLTestClient"]
