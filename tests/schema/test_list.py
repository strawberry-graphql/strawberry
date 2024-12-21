from typing import Optional

import strawberry


def test_basic_list():
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> list[str]:
            return ["Example"]

    schema = strawberry.Schema(query=Query)

    query = "{ example }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["example"] == ["Example"]


def test_of_optional():
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> list[Optional[str]]:
            return ["Example", None]

    schema = strawberry.Schema(query=Query)

    query = "{ example }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["example"] == ["Example", None]


def test_lists_of_lists():
    def get_polygons() -> list[list[float]]:
        return [[2.0, 6.0]]

    @strawberry.type
    class Query:
        polygons: list[list[float]] = strawberry.field(resolver=get_polygons)

    schema = strawberry.Schema(query=Query)

    query = "{ polygons }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["polygons"] == [[2.0, 6.0]]
