from functools import lru_cache

from graphql.language import DocumentNode

from strawberry.extensions.base_extension import Extension
from strawberry.schema.execute import parse_document


def UseParserCache(maxsize: int = None):
    @lru_cache(maxsize=maxsize)
    def cached_parse_document(query: str) -> DocumentNode:
        return parse_document(query)

    class _UseParserCache(Extension):
        def on_parsing_start(self):
            execution_context = self.execution_context

            execution_context.graphql_document = cached_parse_document(
                execution_context.query,
            )

    return _UseParserCache
