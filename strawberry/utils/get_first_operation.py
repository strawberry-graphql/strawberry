from typing import Optional

from graphql.language import DocumentNode, OperationDefinitionNode


def get_first_operation(
    graphql_document: DocumentNode,
) -> Optional[OperationDefinitionNode]:
    for definition in graphql_document.definitions:
        if isinstance(definition, OperationDefinitionNode):
            return definition

    return None
