from __future__ import annotations

import enum


class OperationType(enum.Enum):
    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"

    @staticmethod
    def from_http(method: str) -> set[OperationType]:
        if method == "GET":
            return {OperationType.QUERY}

        if method == "POST":
            return {
                OperationType.QUERY,
                OperationType.MUTATION,
                OperationType.SUBSCRIPTION,
            }

        raise ValueError(f"Unsupported HTTP method: {method}")  # pragma: no cover
