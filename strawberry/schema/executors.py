from typing import TYPE_CHECKING

from graphql import GraphQLError
from rustberry import QueryCompiler

from strawberry import Schema
from strawberry.types.execution import ExecutionContext, Executor

if TYPE_CHECKING:
    from rustberry._rustberry import Document

RUSTBERRY_DOCUMENT_FIELD = "__rustberry_document"


class RustberryExecutor(Executor):
    def __init__(self, schema: Schema) -> None:
        super().__init__(schema)
        self.compiler = QueryCompiler(schema.as_str())

    def parse(self, execution_context: ExecutionContext) -> None:
        document = self.compiler.parse(execution_context.query)
        setattr(execution_context, RUSTBERRY_DOCUMENT_FIELD, document)
        execution_context.graphql_document = self.compiler.gql_core_ast_mirror(document)

    def validate(
        self,
        execution_context: ExecutionContext,
    ) -> None:
        assert execution_context.graphql_document
        document: Document = getattr(execution_context, RUSTBERRY_DOCUMENT_FIELD, None)
        assert document, "Document not set - Required for Rustberry use"
        validation_successful = self.compiler.validate(document)
        if not validation_successful:
            execution_context.errors = execution_context.errors or []
            execution_context.errors.append(GraphQLError("Validation failed"))
