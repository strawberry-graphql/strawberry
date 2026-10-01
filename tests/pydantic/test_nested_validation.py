from typing import Annotated, Any

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.directive import DirectiveLocation, DirectiveValue
from strawberry.pydantic import PydanticValidationErrorHandler, ValidationError


def test_errors_of_nested_inputs_are_reported_together():
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int = pydantic.Field(gt=0)

    @strawberry.pydantic.input
    class CustomerInput(pydantic.BaseModel):
        name: str = pydantic.Field(min_length=1)

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        customer: CustomerInput
        items: list[ItemInput]

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


def test_validators_of_nested_inputs_run_once():
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
        items: list[ItemInput]

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


def test_nested_inputs_have_the_validation_context():
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        sku: str

        @pydantic.field_validator("sku")
        @classmethod
        def check_stock(cls, value: str, info: pydantic.ValidationInfo) -> str:
            if value not in info.context["strawberry_context"]["in_stock"]:
                raise ValueError("out of stock")

            return value

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        items: list[ItemInput]

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self, input: OrderInput) -> int:
            return len(input.items)

    schema = strawberry.Schema(query=Query)

    query = '{ order(input: {items: [{sku: "jam"}, {sku: "tea"}]}) }'

    result = schema.execute_sync(query, context_value={"in_stock": {"jam", "tea"}})

    assert not result.errors
    assert result.data == {"order": 2}

    result = schema.execute_sync(query, context_value={"in_stock": {"jam"}})

    assert result.errors
    assert "items.1.sku" in result.errors[0].message


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


def test_argument_defaults_are_used():
    @strawberry.pydantic.input
    class FilterInput(pydantic.BaseModel):
        limit: int = 10
        name: str | None = None

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: FilterInput = FilterInput(limit=7, name="jam")) -> str:
            return f"{filter.limit} {filter.name}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ search }")

    assert not result.errors
    assert result.data == {"search": "7 jam"}


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
    "wrapper",
    [pydantic.SkipValidation, pydantic.InstanceOf],
    ids=["skip-validation", "instance-of"],
)
def test_nested_inputs_not_validated_as_their_model_are_built_first(wrapper: Any):
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int = pydantic.Field(gt=0)

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        item: Annotated[wrapper[ItemInput], strawberry.field(graphql_type=ItemInput)]

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self, input: OrderInput) -> str:
            return repr(input.item)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ order(input: {item: {quantity: 1}}) }")

    assert not result.errors
    assert result.data == {"order": "ItemInput(quantity=1)"}

    result = schema.execute_sync("{ order(input: {item: {quantity: 0}}) }")

    assert result.errors
    assert result.errors[0].message.startswith("Invalid input: input.item.quantity:")


def test_nested_inputs_with_a_different_graphql_type_are_built_first():
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
    assert result.data == {"user": "USAddressInput(city='NY', zip='10001')"}

    result = schema.execute_sync('{ user(input: {address: {city: "NY", zip: "x"}}) }')

    assert result.errors
    assert result.errors[0].message.startswith("Invalid input: input.address.zip:")


def test_undecorated_subclasses_are_validated_as_themselves():
    @strawberry.pydantic.input
    class FilterInput(pydantic.BaseModel):
        term: str

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


def test_directive_arguments_have_the_validation_context():
    @strawberry.pydantic.input
    class FormatInput(pydantic.BaseModel):
        style: str

        @pydantic.field_validator("style")
        @classmethod
        def check_style(cls, value: str, info: pydantic.ValidationInfo) -> str:
            if value not in info.context["strawberry_context"]["styles"]:
                raise ValueError("unknown style")

            return value

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def formatted(value: DirectiveValue[str], format: FormatInput) -> str:
        return value.upper() if format.style == "upper" else value

    @strawberry.type
    class Query:
        name: str = "jam"

    schema = strawberry.Schema(query=Query, directives=[formatted])

    result = schema.execute_sync(
        '{ name @formatted(format: {style: "upper"}) }',
        root_value=Query(),
        context_value={"styles": {"upper"}},
    )

    assert not result.errors
    assert result.data == {"name": "JAM"}
