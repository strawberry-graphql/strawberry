from __future__ import annotations

import enum
from typing import Set


class OperationType(enum.Enum):
    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"

    @staticmethod
    def from_http(method: str) -> Set[OperationType]:
        # TODO: remove this?
        method = method.lower()

        if method == "get":
            return {OperationType.QUERY}

        if method == "post":
            return {
                OperationType.QUERY,
                OperationType.MUTATION,
                OperationType.SUBSCRIPTION,
            }

        raise ValueError(f"Unsupported HTTP method: {method}")  # pragma: no cover
