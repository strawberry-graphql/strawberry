from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from strawberry.test import BaseGraphQLTestClient

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Literal


class GraphQLTestClient(BaseGraphQLTestClient):
    def _build_body(
        self,
        query: str,
        variables: dict[str, Mapping] | None = None,
        files: dict[str, object] | None = None,
    ) -> dict[str, object]:
        body: dict[str, object] = {"query": query}

        if variables:
            body["variables"] = variables

        if files:
            assert variables is not None
            assert files is not None
            file_map = GraphQLTestClient._build_multipart_file_map(variables, files)

            body = {
                "operations": json.dumps(body),
                "map": json.dumps(file_map),
            }
        return body

    def request(
        self,
        body: dict[str, object],
        headers: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
    ) -> Any:
        return self._client.post(
            self.url,
            json=body if not files else None,
            data=body if files else None,
            files=files,
            headers=headers,
        )

    def _decode(self, response: Any, type: Literal["multipart", "json"]) -> Any:
        return response.json()


__all__ = ["GraphQLTestClient"]
