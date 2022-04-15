from strawberry.types.graphql import OperationType


class InvalidOperationTypeError(Exception):
    def __init__(self, operation_type: OperationType):
        self.operation_type = operation_type
