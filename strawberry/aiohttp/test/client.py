from __future__ import annotations

import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
)

from strawberry.test.client import BaseGraphQLTestClient, Response

if TYPE_CHECKING:
    from collections.abc import Mapping


class GraphQLTestClient(BaseGraphQLTestClient):
    async def query(
        self,
        query: str,
        variables: Optional[dict[str, Mapping]] = None,
        headers: Optional[dict[str, object]] = None,
        asserts_errors: Optional[bool] = None,
        files: Optional[dict[str, object]] = None,
        assert_no_errors: Optional[bool] = True,
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
        headers: Optional[dict[str, object]] = None,
        files: Optional[dict[str, object]] = None,
    ) -> Any:
        return await self._client.post(
            self.url,
            json=body if not files else None,
            data=body if files else None,
        )


__all__ = ["GraphQLTestClient"]
