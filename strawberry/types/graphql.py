from __future__ import annotations

import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strawberry.http.types import HTTPMethod


class OperationType(enum.Enum):
    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"

    @staticmethod
    def from_http(method: HTTPMethod) -> set[OperationType]:
        if method == "GET":
            return {
                OperationType.QUERY,
                # subscriptions are supported via GET in the multipart protocol
                OperationType.SUBSCRIPTION,
            }

        if method == "POST":
            return {
                OperationType.QUERY,
                OperationType.MUTATION,
                OperationType.SUBSCRIPTION,
            }

        raise ValueError(f"Unsupported HTTP method: {method}")  # pragma: no cover


__all__ = ["OperationType"]
