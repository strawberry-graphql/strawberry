import strawberry
from strawberry.extensions import DisableIntrospection


def test_disables_introspection():
    @strawberry.type
    class Query:
        hello: str

    schema = strawberry.Schema(
        query=Query,
        extensions=[DisableIntrospection()],
    )

    result = schema.execute_sync("query { __schema { __typename } }")
    assert result.data is None
    assert result.errors is not None

    formatted_errors = [err.formatted for err in result.errors]
    assert formatted_errors == [
        {
            "message": "GraphQL introspection has been disabled, but the requested query contained the field '__schema'.",
            "locations": [{"line": 1, "column": 9}],
        }
    ]
