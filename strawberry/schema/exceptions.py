from strawberry.types.graphql import OperationType


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


__all__ = ["InvalidOperationTypeError"]
