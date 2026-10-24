import typing
from collections.abc import Sequence
from typing import Annotated, Any

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.pydantic import PydanticValidationErrorHandler, ValidationError

# annotations that Strawberry exposes as GraphQL lists
LIST_ANNOTATIONS = [
    pytest.param(lambda item: list[item], id="list"),
    pytest.param(lambda item: tuple[item, ...], id="tuple"),
    pytest.param(lambda item: Sequence[item], id="sequence"),
]


@pytest.mark.parametrize("list_of", LIST_ANNOTATIONS)
def test_errors_of_nested_inputs_are_reported_together(list_of: Any):
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int = pydantic.Field(gt=0)

    @strawberry.pydantic.input
    class CustomerInput(pydantic.BaseModel):
        name: str = pydantic.Field(min_length=1)

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        customer: CustomerInput
        items: list_of(ItemInput)  # type: ignore[valid-type]

    @strawberry.type
    class Order:
        id: strawberry.ID

    @strawberry.type
    class Query:
        hello: str = "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_order(self, input: OrderInput) -> Order | ValidationError:
            return Order(id=strawberry.ID("1"))

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            createOrder(input: {
                customer: { name: "" }
                items: [{ quantity: 0 }, { quantity: 1 }, { quantity: -1 }]
            }) {
                ... on ValidationError { issues { location type } }
            }
        }
        """
    )

    assert not result.errors
    assert result.data == snapshot(
        {
            "createOrder": {
                "issues": [
                    {
                        "location": ["input", "customer", "name"],
                        "type": "string_too_short",
                    },
                    {
                        "location": ["input", "items", "0", "quantity"],
                        "type": "greater_than",
                    },
                    {
                        "location": ["input", "items", "2", "quantity"],
                        "type": "greater_than",
                    },
                ]
            }
        }
    )


@pytest.mark.parametrize("list_of", LIST_ANNOTATIONS)
def test_validators_of_nested_inputs_run_once(list_of: Any):
    calls: list[int] = []

    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int

        @pydantic.model_validator(mode="after")
        def track(self) -> "ItemInput":
            calls.append(self.quantity)

            return self

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        items: list_of(ItemInput)  # type: ignore[valid-type]

    @strawberry.type
    class Query:
        @strawberry.field
        def total(self, input: OrderInput) -> int:
            return sum(item.quantity for item in input.items)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        "{ total(input: {items: [{quantity: 1}, {quantity: 2}]}) }"
    )

    assert not result.errors
    assert result.data == {"total": 3}
    assert calls == [1, 2]


def test_before_validators_receive_nested_inputs_as_data():
    received: list[Any] = []

    @strawberry.pydantic.input
    class AddressInput(pydantic.BaseModel):
        city: str

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        address: AddressInput

        @pydantic.model_validator(mode="before")
        @classmethod
        def track(cls, data: Any) -> Any:
            received.append(data)

            return data

    @strawberry.type
    class Query:
        @strawberry.field
        def city(self, input: UserInput) -> str:
            return input.address.city

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ city(input: {address: {city: "Rome"}}) }')

    assert not result.errors
    assert result.data == {"city": "Rome"}
    assert received == [{"address": {"city": "Rome"}}]


def test_pydantic_inputs_nested_in_strawberry_inputs_are_validated():
    @strawberry.pydantic.input
    class RangeInput(pydantic.BaseModel):
        start: int
        end: int

        @pydantic.model_validator(mode="after")
        def check_order(self) -> "RangeInput":
            if self.start > self.end:
                raise ValueError("start must be before end")

            return self

    @strawberry.input
    class FilterInput:
        range: RangeInput

    @strawberry.type
    class Query:
        @strawberry.field
        def size(self, filter: FilterInput) -> int:
            return filter.range.end - filter.range.start

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ size(filter: {range: {start: 1, end: 5}}) }")

    assert not result.errors
    assert result.data == {"size": 4}

    result = schema.execute_sync("{ size(filter: {range: {start: 5, end: 1}}) }")

    assert result.errors
    assert "start must be before end" in result.errors[0].message


def test_strawberry_inputs_with_a_model_validate_method_are_not_pydantic():
    @strawberry.input
    class FilterInput:
        name: str

        @classmethod
        def model_validate(cls, data: Any) -> "FilterInput":
            raise AssertionError("shouldn't be called")

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: FilterInput) -> str:
            return filter.name

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ search(filter: {name: "jam"}) }')

    assert not result.errors
    assert result.data == {"search": "jam"}


@pytest.mark.parametrize(
    ("annotation", "requires_instance"),
    [
        (
            lambda model: Annotated[
                pydantic.SkipValidation[model], strawberry.field(graphql_type=model)
            ],
            False,
        ),
        (
            lambda model: Annotated[
                pydantic.InstanceOf[model], strawberry.field(graphql_type=model)
            ],
            True,
        ),
        (lambda model: Annotated[model, pydantic.SkipValidation], False),
        (lambda model: Annotated[model, pydantic.InstanceOf], True),
    ],
    ids=["skip-validation", "instance-of", "bare-skip-validation", "bare-instance-of"],
)
def test_nested_inputs_use_pydantic_validation_semantics(
    annotation: Any, requires_instance: bool
):
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int = pydantic.Field(gt=0)

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        item: annotation(ItemInput)  # type: ignore[valid-type]

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self, input: OrderInput) -> str:
            return repr(input.item)

    schema = strawberry.Schema(query=Query)

    for quantity in (1, 0):
        result = schema.execute_sync(
            "query($input: OrderInput!) { order(input: $input) }",
            variable_values={"input": {"item": {"quantity": quantity}}},
        )

        if requires_instance:
            assert result.errors
            assert result.errors[0].extensions["validationErrors"] == [
                {
                    "location": ["input", "item"],
                    "message": "Input should be an instance of "
                    + ItemInput.__qualname__,
                    "type": "is_instance_of",
                }
            ]
        else:
            assert not result.errors
            assert result.data == {"order": repr({"quantity": quantity})}


@pytest.mark.parametrize("decorator", [False, True], ids=["annotated", "decorator"])
def test_plain_validators_receive_nested_data_before_child_validation(decorator: bool):
    received: list[Any] = []
    validated: list[int] = []

    @strawberry.pydantic.input
    class Child(pydantic.BaseModel):
        n: Annotated[int, strawberry.field(name="number")] = pydantic.Field(gt=4)

        @pydantic.model_validator(mode="after")
        def track(self) -> "Child":
            validated.append(self.n)
            return self

    def double(value: Any) -> Child:
        received.append(value)
        return Child(n=value["n"] * 2)

    if decorator:

        @strawberry.pydantic.input
        class Parent(pydantic.BaseModel):
            child: Child

            @pydantic.field_validator("child", mode="plain")
            @classmethod
            def double_child(cls, value: Any) -> Child:
                return double(value)
    else:

        @strawberry.pydantic.input
        class Parent(pydantic.BaseModel):
            child: Annotated[Child, pydantic.PlainValidator(double)]

    @strawberry.type
    class Query:
        @strawberry.field
        def number(self, input: Parent) -> int:
            return input.child.n

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ number(input: {child: {number: 3}}) }")

    assert not result.errors
    assert result.data == {"number": 6}
    assert received == [{"n": 3}]
    assert validated == [6]


def test_regular_inputs_are_converted_but_nested_models_remain_data():
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int = pydantic.Field(gt=0)

    @strawberry.input
    class LineInput:
        item: ItemInput

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        lines: list[LineInput] = []
        extras: list[Annotated[ItemInput, pydantic.SkipValidation]] = []

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self, input: OrderInput) -> list[str]:
            return [repr(line.item) for line in input.lines] + [
                repr(extra) for extra in input.extras
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        "{ order(input: {lines: [{item: {quantity: 1}}], extras: [{quantity: 2}]}) }"
    )

    assert not result.errors
    assert result.data == {"order": ["ItemInput(quantity=1)", "{'quantity': 2}"]}

    result = schema.execute_sync(
        "{ order(input: {lines: [{item: {quantity: 1}}, {item: {quantity: 0}}]}) }"
    )

    assert result.errors
    assert result.errors[0].message.startswith(
        "Invalid input: input.lines.1.item.quantity:"
    )

    result = schema.execute_sync(
        "{ order(input: {extras: [{quantity: 1}, {quantity: 0}]}) }"
    )

    assert not result.errors
    assert result.data == {"order": ["{'quantity': 1}", "{'quantity': 0}"]}


def test_model_annotation_governs_nested_inputs_with_a_different_graphql_type():
    @strawberry.pydantic.input
    class AddressInput(pydantic.BaseModel):
        city: str

    @strawberry.pydantic.input
    class USAddressInput(AddressInput):
        zip: str = pydantic.Field(pattern=r"^\d{5}$")

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        address: Annotated[AddressInput, strawberry.field(graphql_type=USAddressInput)]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, input: UserInput) -> str:
            return repr(input.address)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        '{ user(input: {address: {city: "NY", zip: "10001"}}) }'
    )

    assert not result.errors
    assert result.data == {"user": "AddressInput(city='NY')"}

    result = schema.execute_sync('{ user(input: {address: {city: "NY", zip: "x"}}) }')

    assert not result.errors
    assert result.data == {"user": "AddressInput(city='NY')"}


@pytest.mark.parametrize(
    "annotation",
    [typing.List, typing.Sequence],  # noqa: UP006
    ids=["list", "sequence"],
)
def test_nested_inputs_in_untyped_lists_remain_data(annotation: Any):
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int = pydantic.Field(gt=0)

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        # pydantic validates the items of bare lists as `Any`
        items: Annotated[  # type: ignore[valid-type]
            annotation, strawberry.field(graphql_type=list[ItemInput])
        ]

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self, input: OrderInput) -> str:
            return repr(input.items)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ order(input: {items: [{quantity: 1}]}) }")

    assert not result.errors
    assert result.data == {"order": "[{'quantity': 1}]"}

    result = schema.execute_sync(
        "{ order(input: {items: [{quantity: 1}, {quantity: 0}]}) }"
    )

    assert not result.errors
    assert result.data == {"order": "[{'quantity': 1}, {'quantity': 0}]"}


def test_decorated_subclasses_are_validated_as_themselves():
    @strawberry.pydantic.input
    class FilterInput(pydantic.BaseModel):
        term: str

    @strawberry.pydantic.input
    class NoSpacesFilterInput(FilterInput):
        @pydantic.field_validator("term")
        @classmethod
        def check_spaces(cls, value: str) -> str:
            if " " in value:
                raise ValueError("no spaces")

            return value

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: NoSpacesFilterInput) -> str:
            return type(filter).__name__

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ search(filter: {term: "jam"}) }')

    assert not result.errors
    assert result.data == {"search": "NoSpacesFilterInput"}

    result = schema.execute_sync('{ search(filter: {term: "strawberry jam"}) }')

    assert result.errors
    assert "no spaces" in result.errors[0].message
