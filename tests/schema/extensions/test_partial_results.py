from dataclasses import dataclass

from graphql import FieldNode, GraphQLError, SourceLocation, located_error

import strawberry
from strawberry.extensions import PartialResultsExtension
from strawberry.types import Info


@dataclass
class Context:
    pass


def test_yes_data_no_errors():
    @strawberry.type
    class Query:
        @strawberry.field
        def id(self, info: Info, id: strawberry.ID) -> strawberry.ID:
            return id

    id = "12345"
    schema = strawberry.Schema(Query, extensions=[PartialResultsExtension])
    result = schema.execute_sync(
        "query ($id: ID!) { id(id: $id) }",
        variable_values={"id": id},
        context_value=Context(),
    )
    data, errors = result.data, result.errors

    assert data["id"] == id
    assert errors is None


def test_no_data_yes_errors():
    @strawberry.type
    class Query:
        @strawberry.field
        def id(self, info: Info) -> strawberry.ID:
            raise Exception("Failure")

    id = "12345"
    schema = strawberry.Schema(Query, extensions=[PartialResultsExtension])
    result = schema.execute_sync(
        "query { id }",
        variable_values={"id": id},
        context_value=Context(),
    )
    data, errors = result.data, result.errors

    assert data is None
    assert len(errors) == 1
    error: GraphQLError = errors[0]
    assert error.message == "Failure"
    assert error.locations == [SourceLocation(line=1, column=9)]
    assert error.path == ["id"]
    assert len(error.nodes) == 1
    assert isinstance(error.nodes[0], FieldNode)
    assert error.positions == [8]
    assert error.extensions == {}
    assert isinstance(error.original_error, Exception)
    assert str(error.original_error) == "Failure"
    # the actual json in the response
    assert error.formatted == {
        "message": "Failure",
        "locations": [{"line": 1, "column": 9}],
        "path": ["id"],
    }


def test_yes_data_yes_errors():
    @strawberry.type
    class Query:
        @strawberry.field
        def id(self, info: Info, id: strawberry.ID) -> strawberry.ID:
            nodes = [next(n for n in info.field_nodes if n.name.value == "id")]
            info.context.partial_errors.extend(
                [
                    Exception("Raw Exception"),
                    located_error(
                        Exception("Located error"),
                        nodes=nodes,
                        path=info.path.as_list(),
                    ),
                    located_error(Exception("Located error without any location data")),
                    GraphQLError(
                        "Raw GraphQLError with extensions", extensions={"foo": "bar"}
                    ),
                ],
            )
            return id

    id = "12345"
    schema = strawberry.Schema(Query, extensions=[PartialResultsExtension])
    result = schema.execute_sync(
        "query ($id: ID!) { id(id: $id) }",
        variable_values={"id": id},
        context_value=Context(),
    )
    data, errors = result.data, result.errors

    assert data["id"] == id

    assert len(errors) == 4

    error0: GraphQLError = errors[0]
    assert error0.message == "Raw Exception"
    assert error0.locations is None
    assert error0.path is None
    assert error0.nodes is None
    assert error0.positions is None
    assert error0.extensions == {}
    assert isinstance(error0.original_error, Exception)
    assert str(error0.original_error) == "Raw Exception"
    # the actual json in the response
    assert error0.formatted == {
        "message": "Raw Exception",
    }

    error1: GraphQLError = errors[1]
    assert error1.message == "Located error"
    assert error1.locations == [SourceLocation(line=1, column=20)]
    assert error1.path == ["id"]
    assert len(error1.nodes) == 1
    assert isinstance(error1.nodes[0], FieldNode)
    assert error1.positions == [19]
    assert error1.extensions == {}
    assert isinstance(error1.original_error, Exception)
    assert str(error1.original_error) == "Located error"
    # the actual json in the response
    assert error1.formatted == {
        "message": "Located error",
        "locations": [{"line": 1, "column": 20}],
        "path": ["id"],
    }

    error2: GraphQLError = errors[2]
    assert error2.message == "Located error without any location data"
    assert error2.locations is None
    assert error2.path is None
    assert error2.nodes is None
    assert error2.positions is None
    assert error2.extensions == {}
    assert isinstance(error2.original_error, Exception)
    assert str(error2.original_error) == "Located error without any location data"
    # the actual json in the response
    assert error2.formatted == {
        "message": "Located error without any location data",
    }

    error3: GraphQLError = errors[3]
    assert error3.message == "Raw GraphQLError with extensions"
    assert error3.locations is None
    assert error3.path is None
    assert error3.nodes is None
    assert error3.positions is None
    assert error3.extensions == {"foo": "bar"}
    assert error3.original_error is None
    # the actual json in the response
    assert error3.formatted == {
        "message": "Raw GraphQLError with extensions",
        "extensions": {"foo": "bar"},
    }
