import strawberry
from strawberry.extensions import SchemaExtension


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"


def test_execution_context_operation_name_and_type():
    operation_name = None
    operation_type = None

    class MyExtension(SchemaExtension):
        def on_operation(self):
            yield
            nonlocal operation_name
            nonlocal operation_type

            execution_context = self.execution_context

            operation_name = execution_context.operation_name
            operation_type = execution_context.operation_type.value

    schema = strawberry.Schema(Query, extensions=[MyExtension])

    result = schema.execute_sync("{ ping }")
    assert not result.errors

    assert operation_name is None
    assert operation_type == "query"

    # Try again with an operation_name
    result = schema.execute_sync("query MyOperation { ping }")
    assert not result.errors

    assert operation_name == "MyOperation"
    assert operation_type == "query"

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
    assert operation_type == "query"


def test_execution_context_operation_type_mutation():
    operation_name = None
    operation_type = None

    class MyExtension(SchemaExtension):
        def on_operation(self):
            yield
            nonlocal operation_name
            nonlocal operation_type

            execution_context = self.execution_context

            operation_name = execution_context.operation_name
            operation_type = execution_context.operation_type.value

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def my_mutation(self) -> str:
            return "hi"

    schema = strawberry.Schema(Query, mutation=Mutation, extensions=[MyExtension])

    result = schema.execute_sync("mutation { myMutation }")
    assert not result.errors

    assert operation_name is None
    assert operation_type == "mutation"

    # Try again with an operation_name
    result = schema.execute_sync("mutation MyMutation { myMutation }")
    assert not result.errors

    assert operation_name == "MyMutation"
    assert operation_type == "mutation"

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
    assert operation_type == "mutation"


def test_execution_context_operation_name_and_type_with_fragments():
    operation_name = None
    operation_type = None

    class MyExtension(SchemaExtension):
        def on_operation(self):
            yield
            nonlocal operation_name
            nonlocal operation_type

            execution_context = self.execution_context

            operation_name = execution_context.operation_name
            operation_type = execution_context.operation_type.value

    schema = strawberry.Schema(Query, extensions=[MyExtension])

    result = schema.execute_sync(
        """
        fragment MyFragment on Query {
            ping
        }

        query MyOperation {
            ping
            ...MyFragment
        }
        """
    )
    assert not result.errors

    assert operation_name == "MyOperation"
    assert operation_type == "query"


def test_error_when_accessing_operation_type_before_parsing():
    class MyExtension(SchemaExtension):
        def on_operation(self):
            execution_context = self.execution_context

            # This should raise a RuntimeError
            execution_context.operation_type

    schema = strawberry.Schema(Query, extensions=[MyExtension])

    result = schema.execute_sync("mutation { myMutation }")
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, RuntimeError)
    assert result.errors[0].message == "No GraphQL document available"


def test_error_when_accessing_operation_type_with_invalid_operation_name():
    class MyExtension(SchemaExtension):
        def on_parse(self):
            yield
            execution_context = self.execution_context

            # This should raise a RuntimeError
            execution_context.operation_type

    schema = strawberry.Schema(Query, extensions=[MyExtension])

    result = schema.execute_sync("query { ping }", operation_name="MyQuery")
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, RuntimeError)
    assert result.errors[0].message == "Can't get GraphQL operation type"
