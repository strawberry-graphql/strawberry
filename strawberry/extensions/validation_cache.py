from functools import lru_cache
from typing import List, Tuple, Type

from graphql import ASTValidationRule, GraphQLError, GraphQLSchema
from graphql.language import DocumentNode

from strawberry.extensions.base_extension import Extension
from strawberry.schema.execute import validate_document


def UseValidationCache(maxsize: int = None):
    @lru_cache(maxsize=maxsize)
    def cached_validate_document(
        schema: GraphQLSchema,
        document: DocumentNode,
        validation_rules: Tuple[Type[ASTValidationRule], ...],
    ) -> List[GraphQLError]:
        return validate_document(schema, document, validation_rules)

    class _UseValidationCache(Extension):
        def on_validation_start(self):
            execution_context = self.execution_context

            errors = cached_validate_document(
                execution_context.graphql_schema,
                execution_context.graphql_document,
                execution_context.validation_rules,
            )
            execution_context.errors = errors

    return _UseValidationCache
