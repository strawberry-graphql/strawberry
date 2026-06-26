from typing import Any

import pytest

import strawberry


def test_can_use_info_with_two_arguments():
    CustomInfo = strawberry.Info[int, str]

    assert CustomInfo.__args__ == (int, str)


def test_can_use_info_with_one_argument():
    CustomInfo = strawberry.Info[int]

    assert CustomInfo.__args__ == (int, Any)


def test_cannot_use_info_with_more_than_two_arguments():
    with pytest.raises(
        TypeError,
        match=r"Too many (arguments|parameters) for <class '.*.Info'>; actual 3, expected 2",
    ):
        strawberry.Info[int, str, int]  # type: ignore


def test_field_args_direct_scalar():
    captured_args = {}

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def test_field(info: strawberry.Info, arg1: str, second_arg: int) -> str:
            nonlocal captured_args
            captured_args = info.field_args
            return "result"

    schema = strawberry.Schema(query=Query)
    query = 'query { testField(arg1: "value1", secondArg: 123) }'

    result = schema.execute_sync(query)

    assert result.errors is None
    assert captured_args == {"arg1": "value1", "second_arg": 123}


def test_field_args_variable_scalar():
    captured_args = {}

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def test_field(info: strawberry.Info, arg1: str, arg2: int) -> str:
            nonlocal captured_args
            captured_args = info.field_args
            return "result"

    schema = strawberry.Schema(query=Query)
    query = "query ($v1: String!, $v2: Int!) { testField(arg1: $v1, arg2: $v2) }"
    variable_values = {"v1": "value1", "v2": 123}

    result = schema.execute_sync(query, variable_values=variable_values)

    assert result.errors is None
    assert captured_args == {"arg1": "value1", "arg2": 123}


def test_field_args_direct_input():
    captured_args = {}

    @strawberry.input
    class TestInput:
        name: str
        value: int

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def test_field(info: strawberry.Info, data: TestInput) -> str:
            nonlocal captured_args
            captured_args = info.field_args
            return "result"

    schema = strawberry.Schema(query=Query)
    query = 'query { testField(data: { name: "test", value: 42 }) }'

    result = schema.execute_sync(query)

    assert result.errors is None
    assert captured_args == {"data": TestInput(name="test", value=42)}


def test_field_args_variable_input():
    captured_args = {}

    @strawberry.input
    class TestInput:
        name: str
        value: int

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def test_field(info: strawberry.Info, data: TestInput) -> str:
            nonlocal captured_args
            captured_args = info.field_args
            return "result"

    schema = strawberry.Schema(query=Query)
    query = "query ($data: TestInput!) { testField(data: $data) }"
    variables = {"data": {"name": "var", "value": 7}}

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors is None
    assert captured_args == {"data": TestInput(name="var", value=7)}


def test_field_args_direct_nested_input():
    captured_args = {}

    @strawberry.input
    class ChildInput:
        title: str
        count: int

    @strawberry.input
    class ParentInput:
        child: ChildInput

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def test_field(info: strawberry.Info, data: ParentInput) -> str:
            nonlocal captured_args
            captured_args = info.field_args
            return "done"

    schema = strawberry.Schema(query=Query)
    query = 'query { testField(data: { child: { title: "x", count: 2 } }) }'

    result = schema.execute_sync(query)

    assert result.errors is None
    assert captured_args == {"data": ParentInput(child=ChildInput(title="x", count=2))}


def test_field_args_variable_nested_input():
    captured_args = {}

    @strawberry.input
    class ChildInput:
        title: str
        count: int

    @strawberry.input
    class ParentInput:
        child: ChildInput

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def test_field(info: strawberry.Info, data: ParentInput) -> str:
            nonlocal captured_args
            captured_args = info.field_args
            return "ok"

    schema = strawberry.Schema(query=Query)
    query = "query ($data: ParentInput!) { testField(data: $data) }"
    variables = {"data": {"child": {"title": "y", "count": 5}}}

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors is None
    assert captured_args == {"data": ParentInput(child=ChildInput(title="y", count=5))}


def test_field_args_direct_list_of_input():
    captured_args = {}

    @strawberry.input
    class ItemInput:
        name: str
        qty: int

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def test_field(info: strawberry.Info, items: list[ItemInput]) -> str:
            nonlocal captured_args
            captured_args = info.field_args
            return "ok"

    schema = strawberry.Schema(query=Query)
    query = 'query { testField(items: [{ name: "a", qty: 1 }, { name: "b", qty: 2 }]) }'

    result = schema.execute_sync(query)

    assert result.errors is None
    assert captured_args == {
        "items": [ItemInput(name="a", qty=1), ItemInput(name="b", qty=2)]
    }


def test_field_args_variable_list_of_inputs():
    captured_args = {}

    @strawberry.input
    class ItemInput:
        name: str
        qty: int

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def test_field(info: strawberry.Info, items: list[ItemInput]) -> str:
            nonlocal captured_args
            captured_args = info.field_args
            return "ok"

    schema = strawberry.Schema(query=Query)
    query = "query ($items: [ItemInput!]!) { testField(items: $items) }"
    variables = {"items": [{"name": "c", "qty": 3}, {"name": "d", "qty": 4}]}

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors is None
    assert captured_args == {
        "items": [ItemInput(name="c", qty=3), ItemInput(name="d", qty=4)]
    }


def test_field_args_maybe_unset_handling():
    captured_args = {}

    @strawberry.input
    class MaybeInput:
        required: str
        maybe: strawberry.Maybe[str]
        maybe_null: strawberry.Maybe[str | None]
        optional: str | None = strawberry.UNSET

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def test_field(info: strawberry.Info, data: MaybeInput) -> str:
            nonlocal captured_args
            captured_args = info.field_args
            return "ok"

    schema = strawberry.Schema(query=Query)

    # Case 1: All fields provided
    query_1 = (
        'query { testField(data: { required: "req", optional: "opt", '
        'maybe: "may", maybeNull: "mayNull" }) }'
    )
    result = schema.execute_sync(query_1)
    assert result.errors is None
    assert captured_args["data"] == MaybeInput(
        required="req",
        optional="opt",
        maybe=strawberry.Some("may"),
        maybe_null=strawberry.Some("mayNull"),
    )

    # Case 2: Optional and Maybe fields omitted (UNSET)
    query_2 = 'query { testField(data: { required: "req" }) }'
    result = schema.execute_sync(query_2)
    assert result.errors is None
    assert captured_args["data"] == MaybeInput(
        required="req", maybe=None, maybe_null=None, optional=strawberry.UNSET
    )

    # Case 3: Explicit null for maybeNull
    query_3 = 'query { testField(data: { required: "req", maybeNull: null }) }'
    result = schema.execute_sync(query_3)
    assert result.errors is None
    assert captured_args["data"] == MaybeInput(
        required="req",
        maybe=None,
        maybe_null=strawberry.Some(None),
        optional=strawberry.UNSET,
    )
