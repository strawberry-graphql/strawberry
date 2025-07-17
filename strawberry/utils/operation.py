from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from graphql.language import OperationDefinitionNode

from strawberry.types.graphql import OperationType

if TYPE_CHECKING:
    from graphql.language import DocumentNode


def get_first_operation(
    graphql_document: DocumentNode,
) -> Optional[OperationDefinitionNode]:
    for definition in graphql_document.definitions:
        if isinstance(definition, OperationDefinitionNode):
            return definition

    return None


def get_operation_type(
    graphql_document: DocumentNode, operation_name: Optional[str] = None
) -> OperationType:
    definition: Optional[OperationDefinitionNode] = None

    if operation_name is not None:
        for d in graphql_document.definitions:
            if not isinstance(d, OperationDefinitionNode):
                continue
            if d.name and d.name.value == operation_name:
                definition = d
                break
    else:
        definition = get_first_operation(graphql_document)

    if not definition:
        raise RuntimeError("Can't get GraphQL operation type")

    return OperationType(definition.operation.value)


__all__ = ["get_first_operation", "get_operation_type"]
