from __future__ import annotations

import warnings
from typing import Any

from strawberry.test.client import BaseGraphQLTestClient, Response


class GraphQLTestClient(BaseGraphQLTestClient):
    async def query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        headers: dict[str, object] | None = None,
        asserts_errors: bool | None = None,
        files: dict[str, object] | None = None,
        assert_no_errors: bool | None = True,
    ) -> Response:
        body = self._build_body(query, variables, files)

        resp = await self.request(body, headers, files)
        data = await resp.json()

        response = Response(
            errors=data.get("errors"),
            data=data.get("data"),
            extensions=data.get("extensions"),
        )

        if asserts_errors is not None:
            warnings.warn(
                "The `asserts_errors` argument has been renamed to `assert_no_errors`",
                DeprecationWarning,
                stacklevel=2,
            )

        assert_no_errors = (
            assert_no_errors if asserts_errors is None else asserts_errors
        )

        if assert_no_errors:
            assert resp.status == 200
            assert response.errors is None

        return response

    async def request(
        self,
        body: dict[str, object],
        headers: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
    ) -> Any:
        return await self._client.post(
            self.url,
            json=body if not files else None,
            data=body if files else None,
        )


__all__ = ["GraphQLTestClient"]
