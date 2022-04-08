from typing import Optional
from graphql import DocumentNode, OperationDefinitionNode, OperationType, parse


# Move this. Query is already being parsed
def resolve_operation_type(
    query: str, operation_name: Optional[str] = None
) -> OperationType:
    node: DocumentNode = parse(query)
    definition: OperationDefinitionNode = node.definitions[0]

    return definition.operation
