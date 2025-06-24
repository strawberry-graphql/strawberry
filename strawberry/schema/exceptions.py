from typing import Optional

from strawberry.types.graphql import OperationType


class CannotGetOperationTypeError(Exception):
    """Internal error raised when we cannot get the operation type from a GraphQL document."""

    def __init__(self, operation_name: Optional[str]) -> None:
        self.operation_name = operation_name

    def as_http_error_reason(self) -> str:
        return (
            "Can't get GraphQL operation type"
            if self.operation_name is None
            else f'Unknown operation named "{self.operation_name}".'
        )


class InvalidOperationTypeError(Exception):
    def __init__(self, operation_type: OperationType) -> None:
        self.operation_type = operation_type

    def as_http_error_reason(self, method: str) -> str:
        operation_type = {
            OperationType.QUERY: "queries",
            OperationType.MUTATION: "mutations",
            OperationType.SUBSCRIPTION: "subscriptions",
        }[self.operation_type]

        return f"{operation_type} are not allowed when using {method}"


__all__ = [
    "CannotGetOperationTypeError",
    "InvalidOperationTypeError",
]
