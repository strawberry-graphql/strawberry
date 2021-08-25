from functools import lru_cache
from typing import Collection, Type

from graphql import GraphQLSchema, ValidationRule, validate
from graphql.language import DocumentNode

from strawberry.extensions.base_extension import Extension


def ValidationCacheExtension(maxsize: int = None):
    @lru_cache(maxsize=maxsize)
    def validate_query(
        schema: GraphQLSchema,
        document: DocumentNode,
        validation_rules: Collection[Type[ValidationRule]],
    ):
        return validate(schema, document, rules=validation_rules)

    class _ValidationCacheExtension(Extension):
        def on_validation_start(self):
            execution_context = self.execution_context

            errors = validate_query(
                execution_context.graphql_schema,
                execution_context.graphql_document,
                execution_context.validation_rules,
            )
            execution_context.errors = errors

    return _ValidationCacheExtension
