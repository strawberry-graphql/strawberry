from typing import TYPE_CHECKING

from graphql import GraphQLError
from rustberry import QueryCompiler

from strawberry import Schema
from strawberry.types.execution import ExecutionContext, Executor

if TYPE_CHECKING:
    from rustberry._rustberry import FileId


RUSTBERRY_FILE_ID_FIELD = "__rustberry_file_id"


class RustberryExecutor(Executor):
    def __init__(self, schema: Schema):
        super().__init__(schema)
        self.compiler = QueryCompiler()
        self.compiler.set_schema(schema.as_str())

    def parse(self, execution_context: ExecutionContext):
        file_id = self.compiler.add_executable(execution_context.query)
        setattr(execution_context, RUSTBERRY_FILE_ID_FIELD, file_id)
        execution_context.graphql_document = self.compiler.gql_core_ast_mirror(file_id)

    def validate(
        self,
        execution_context: ExecutionContext,
    ):
        assert execution_context.graphql_document
        file_id: FileId = getattr(execution_context, RUSTBERRY_FILE_ID_FIELD, None)
        assert file_id, "File ID not set - Required for Rustberry use"
        validation_successful = self.compiler.validate_file(file_id)
        if not validation_successful:
            execution_context.errors = execution_context.errors or []
            execution_context.errors.append(GraphQLError("Validation failed"))
