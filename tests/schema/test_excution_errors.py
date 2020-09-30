import strawberry
from strawberry.extensions import Extension


class MyExtension(Extension):
    def get_results(self):
        return {"example": "example"}


def test_runs_schema_validation():
    @strawberry.type
    class Query:
        ...

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
        }
    """

    result = schema.execute_sync(query)

    assert len(result.errors) == 1
    assert result.errors[0].message == "Type Query must define one or more fields."


def test_runs_parsing():
    @strawberry.type
    class Query:
        name: str

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
    """

    result = schema.execute_sync(query)

    assert len(result.errors) == 1
    assert result.errors[0].message == "Syntax Error: Expected Name, found <EOF>."


def test_handles_exceptions():
    @strawberry.type
    class Query:
        @strawberry.field
        def fail(self) -> str:
            raise ValueError("Custom runtime error")

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            fail
        }
    """

    result = schema.execute_sync(query)

    assert len(result.errors) == 1
    assert result.errors[0].message == "Custom runtime error"
