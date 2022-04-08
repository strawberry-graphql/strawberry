from typing import Optional

from graphql import DocumentNode, OperationDefinitionNode, OperationType


# Move this. Query is already being parsed
def resolve_operation_type(
    document: DocumentNode, operation_name: Optional[str] = None
) -> OperationType:
    definition: OperationDefinitionNode = document.definitions[0]

    return definition.operation
