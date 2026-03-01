from enum import Enum

import strawberry
from strawberry import UNSET, Maybe, Some, asdict


def test_simple_type():
    @strawberry.type
    class User:
        name: str
        age: int

    assert asdict(User(name="Alex", age=30)) == {"name": "Alex", "age": 30}


def test_input_type():
    @strawberry.input
    class Input:
        title: str
        description: str
        tags: list[str] | None = strawberry.field(default=None)

    assert asdict(Input(title="foo", description="bar")) == {
        "title": "foo",
        "description": "bar",
        "tags": None,
    }


def test_type_with_nested_type_and_enum_in_list():
    @strawberry.enum
    class Count(Enum):
        TWO = "two"
        FOUR = "four"

    @strawberry.type
    class Animal:
        legs: Count

    @strawberry.type
    class People:
        name: str
        animals: list[Animal]

    assert asdict(
        People(name="Kevin", animals=[Animal(legs=Count.TWO), Animal(legs=Count.FOUR)])
    ) == {
        "name": "Kevin",
        "animals": [{"legs": Count.TWO}, {"legs": Count.FOUR}],
    }


def test_unset_field_is_excluded():
    @strawberry.input
    class Input:
        field: str | None

    assert asdict(Input(field=None)) == {"field": None}
    assert asdict(Input(field=UNSET)) == {}


def test_unset_field_in_nested_input_is_excluded():
    @strawberry.input
    class InnerInput:
        field: str | None

    @strawberry.input
    class OuterInput:
        nested: InnerInput

    assert asdict(OuterInput(nested=InnerInput(field=UNSET))) == {"nested": {}}


def test_maybe_field_absent_is_excluded():
    @strawberry.input
    class Input:
        field: Maybe[str | None]

    assert asdict(Input(field=None)) == {}


def test_maybe_field_unset_is_excluded():
    @strawberry.input
    class Input:
        field: Maybe[str | None]

    assert asdict(Input(field=UNSET)) == {}


def test_maybe_field_with_some_value():
    @strawberry.input
    class Input:
        field: Maybe[str | None]

    assert asdict(Input(field=Some("foo"))) == {"field": "foo"}


def test_maybe_field_with_some_none():
    @strawberry.input
    class Input:
        field: Maybe[str | None]

    assert asdict(Input(field=Some(None))) == {"field": None}


def test_multiple_maybe_fields_partial():
    @strawberry.input
    class Input:
        field_a: Maybe[str | None]
        field_b: Maybe[str | None]
        field_c: Maybe[str | None]

    # field_b is absent (None default), so it should be excluded
    assert asdict(
        Input(field_a=Some("hello"), field_b=None, field_c=Some("world"))
    ) == {
        "field_a": "hello",
        "field_c": "world",
    }


def test_nested_input():
    @strawberry.input
    class InnerInput:
        field: str

    @strawberry.input
    class OuterInput:
        scalar: str
        nested: InnerInput

    assert asdict(OuterInput(scalar="foo", nested=InnerInput(field="bar"))) == {
        "scalar": "foo",
        "nested": {"field": "bar"},
    }


def test_nested_input_three_levels_deep():
    @strawberry.input
    class Level3:
        field: str

    @strawberry.input
    class Level2:
        nested: Level3

    @strawberry.input
    class Level1:
        nested: Level2

    assert asdict(Level1(nested=Level2(nested=Level3(field="deep")))) == {
        "nested": {"nested": {"field": "deep"}}
    }


def test_optional_nested_input():
    @strawberry.input
    class InnerInput:
        field: str

    @strawberry.input
    class OuterInput:
        nested: InnerInput | None = None

    assert asdict(OuterInput()) == {"nested": None}
    assert asdict(OuterInput(nested=InnerInput(field="foo"))) == {
        "nested": {"field": "foo"}
    }


def test_maybe_nested_input():
    @strawberry.input
    class InnerInput:
        field: str

    @strawberry.input
    class OuterInput:
        nested: Maybe[InnerInput]

    assert asdict(OuterInput(nested=Some(InnerInput(field="foo")))) == {
        "nested": {"field": "foo"}
    }


def test_maybe_nested_input_explicitly_null():
    @strawberry.input
    class InnerInput:
        field: str

    @strawberry.input
    class OuterInput:
        nested: Maybe[InnerInput | None]

    assert asdict(OuterInput(nested=Some(None))) == {"nested": None}


def test_nested_input_with_maybe_field():
    @strawberry.input
    class InnerInput:
        required_field: str
        optional_field: Maybe[str | None]

    @strawberry.input
    class OuterInput:
        nested: InnerInput

    assert asdict(OuterInput(nested=InnerInput(required_field="foo"))) == {
        "nested": {"required_field": "foo"}
    }
    assert asdict(
        OuterInput(nested=InnerInput(required_field="foo", optional_field=Some("bar")))
    ) == {"nested": {"required_field": "foo", "optional_field": "bar"}}


def test_maybe_nested_input_with_unset_inner_field():
    @strawberry.input
    class InnerInput:
        required_field: str
        optional_field: str | None

    @strawberry.input
    class OuterInput:
        nested: Maybe[InnerInput]

    assert asdict(
        OuterInput(nested=Some(InnerInput(required_field="foo", optional_field=UNSET)))
    ) == {"nested": {"required_field": "foo"}}


def test_empty_list():
    @strawberry.input
    class Input:
        items: list[str]

    assert asdict(Input(items=[])) == {"items": []}


def test_empty_tuple():
    @strawberry.input
    class Input:
        items: tuple[str, ...]

    assert asdict(Input(items=())) == {"items": []}


def test_list_with_none_items():
    @strawberry.input
    class Input:
        items: list[str | None]

    assert asdict(Input(items=["a", None, "b"])) == {"items": ["a", None, "b"]}


def test_list_of_nested_inputs():
    @strawberry.input
    class InnerInput:
        field: str

    @strawberry.input
    class OuterInput:
        items: list[InnerInput]

    assert asdict(
        OuterInput(items=[InnerInput(field="foo"), InnerInput(field="bar")])
    ) == {"items": [{"field": "foo"}, {"field": "bar"}]}


def test_tuple_of_nested_inputs():
    @strawberry.input
    class InnerInput:
        field: str

    @strawberry.input
    class OuterInput:
        items: tuple[InnerInput, ...]

    assert asdict(
        OuterInput(items=(InnerInput(field="foo"), InnerInput(field="bar")))
    ) == {"items": [{"field": "foo"}, {"field": "bar"}]}


def test_list_of_optional_nested_inputs():
    @strawberry.input
    class InnerInput:
        field: str

    @strawberry.input
    class OuterInput:
        items: list[InnerInput | None]

    assert asdict(
        OuterInput(items=[InnerInput(field="foo"), None, InnerInput(field="bar")])
    ) == {"items": [{"field": "foo"}, None, {"field": "bar"}]}


def test_enum_values_in_list():
    @strawberry.enum
    class Status(Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    @strawberry.type
    class Result:
        statuses: list[Status]

    assert asdict(Result(statuses=[Status.ACTIVE, Status.INACTIVE])) == {
        "statuses": [Status.ACTIVE, Status.INACTIVE]
    }


def test_maybe_list():
    @strawberry.input
    class InnerInput:
        field: str

    @strawberry.input
    class OuterInput:
        items: Maybe[list[InnerInput]]

    assert asdict(
        OuterInput(items=Some([InnerInput(field="foo"), InnerInput(field="bar")]))
    ) == {"items": [{"field": "foo"}, {"field": "bar"}]}


def test_maybe_list_with_none_items():
    @strawberry.input
    class Input:
        items: Maybe[list[str | None]]

    assert asdict(Input(items=Some([None, "foo", None]))) == {
        "items": [None, "foo", None]
    }


def test_optional_list():
    @strawberry.input
    class Input:
        items: list[str] | None = None

    assert asdict(Input()) == {"items": None}
    assert asdict(Input(items=["a", "b"])) == {"items": ["a", "b"]}
