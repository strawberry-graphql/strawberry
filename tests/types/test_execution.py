import strawberry
from strawberry.extensions import Extension


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"


def test_execution_context_operation_name_and_type():
    operation_name = None
    operation_type = None

    class MyExtension(Extension):
        def on_request_end(self):
            nonlocal operation_name
            nonlocal operation_type

            execution_context = self.execution_context

            operation_name = execution_context.operation_name
            operation_type = execution_context.operation_type

    schema = strawberry.Schema(Query, extensions=[MyExtension])

    result = schema.execute_sync("{ ping }")
    assert not result.errors

    assert operation_name is None
    assert operation_type == "QUERY"

    # Try again with an operation_name
    result = schema.execute_sync("query MyOperation { ping }")
    assert not result.errors

    assert operation_name == "MyOperation"
    assert operation_type == "QUERY"

    # Try again with an operation_name override
    result = schema.execute_sync(
        """
        query MyOperation { ping }
        query MyOperation2 { ping }
        """,
        operation_name="MyOperation2",
    )
    assert not result.errors

    assert operation_name == "MyOperation2"
    assert operation_type == "QUERY"


def test_execution_context_operation_type_mutation():
    operation_name = None
    operation_type = None

    class MyExtension(Extension):
        def on_request_end(self):
            nonlocal operation_name
            nonlocal operation_type

            execution_context = self.execution_context

            operation_name = execution_context.operation_name
            operation_type = execution_context.operation_type

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def my_mutation(self) -> str:
            return "hi"

    schema = strawberry.Schema(Query, mutation=Mutation, extensions=[MyExtension])

    result = schema.execute_sync("mutation { myMutation }")
    assert not result.errors

    assert operation_name is None
    assert operation_type == "MUTATION"

    # Try again with an operation_name
    result = schema.execute_sync("mutation MyMutation { myMutation }")
    assert not result.errors

    assert operation_name == "MyMutation"
    assert operation_type == "MUTATION"

    # Try again with an operation_name override
    result = schema.execute_sync(
        """
        mutation MyMutation { myMutation }
        mutation MyMutation2 { myMutation }
        """,
        operation_name="MyMutation2",
    )
    assert not result.errors

    assert operation_name == "MyMutation2"
    assert operation_type == "MUTATION"
