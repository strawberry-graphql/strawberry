from __future__ import annotations

import warnings
from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
)

from strawberry.test.client import BaseGraphQLTestClient, Response


class GraphQLTestClient(BaseGraphQLTestClient):
    async def query(
        self,
        query: str,
        variables: Optional[Dict[str, Mapping]] = None,
        headers: Optional[Dict[str, object]] = None,
        asserts_errors: Optional[bool] = None,
        files: Optional[Dict[str, object]] = None,
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
        body: Dict[str, object],
        headers: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, object]] = None,
    ) -> Any:
        response = await self._client.post(
            self.url,
            json=body if not files else None,
            data=body if files else None,
        )

        return response


__all__ = ["GraphQLTestClient"]
