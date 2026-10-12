import datetime as dt
import decimal
import typing
import uuid
from collections.abc import Sequence
from enum import Enum
from typing import Annotated, Any, Self

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.pydantic.exceptions import (
    MaybeFieldError,
    UnsupportedInheritedFieldError,
)
from strawberry.scalars import JSON


class Color(Enum):
    RED = "red"
    BLUE = "blue"


def _input_sdl(schema: strawberry.Schema, name: str) -> str:
    sdl = str(schema)
    start = sdl.index(f"input {name} ")

    return sdl[start : sdl.index("\n}", start) + 2]


def test_constant_defaults_are_published():
    @strawberry.enum
    class Size(Enum):
        SMALL = "small"
        LARGE = "large"

    @strawberry.pydantic.input
    class SearchInput(pydantic.BaseModel):
        query: str = ""
        page_size: int = 20
        min_score: float = 0.5
        exact: bool = False
        size: Size = Size.SMALL
        tags: list[str] = ["new"]
        labels: Sequence[str] = ["sale"]

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, input: SearchInput) -> str:
            return input.model_dump_json()

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "SearchInput") == snapshot("""\
input SearchInput {
  query: String! = ""
  pageSize: Int! = 20
  minScore: Float! = 0.5
  exact: Boolean! = false
  size: Size! = SMALL
  tags: [String!]! = ["new"]
  labels: [String!]! = ["sale"]
}\
""")

    result = schema.execute_sync("{ search(input: {}) }")

    assert not result.errors
    assert result.data == {
        "search": (
            '{"query":"","page_size":20,"min_score":0.5,"exact":false,'
            '"size":"small","tags":["new"],"labels":["sale"]}'
        )
    }


def test_none_defaults_match_strawberry_inputs():
    @strawberry.pydantic.input
    class UpdateUserInput(pydantic.BaseModel):
        name: str | None = None
        bio: str | None = None

    @strawberry.type
    class Query:
        @strawberry.field
        def update_user(self, input: UpdateUserInput) -> str:
            return repr(input.model_dump(exclude_unset=True))

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "UpdateUserInput") == snapshot("""\
input UpdateUserInput {
  name: String = null
  bio: String = null
}\
""")

    @strawberry.input(name="UpdateUserInput")
    class PlainInput:
        name: str | None = None
        bio: str | None = None

    @strawberry.type
    class PlainQuery:
        @strawberry.field
        def update_user(self, input: PlainInput) -> str:
            return repr(input)

    assert _input_sdl(schema, "UpdateUserInput") == _input_sdl(
        strawberry.Schema(query=PlainQuery), "UpdateUserInput"
    )

    # GraphQL supplies published defaults before Pydantic validates the input.
    result = schema.execute_sync('{ updateUser(input: {bio: "Hi"}) }')

    assert not result.errors
    assert result.data == {"updateUser": "{'name': None, 'bio': 'Hi'}"}

    # an explicit null is set, so it can be used to clear a value
    result = schema.execute_sync("{ updateUser(input: {name: null}) }")

    assert not result.errors
    assert result.data == {"updateUser": "{'name': None, 'bio': None}"}


def test_default_factories_run_for_every_request():
    calls = 0

    def next_number() -> int:
        nonlocal calls
        calls += 1

        return calls

    @strawberry.pydantic.input
    class CreateOrderInput(pydantic.BaseModel):
        id: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)
        number: int = pydantic.Field(default_factory=next_number)
        reference: str = pydantic.Field(default_factory=lambda data: str(data["id"]))

    # factories are applied by pydantic, not when the class is decorated
    assert calls == 0

    @strawberry.type
    class Query:
        @strawberry.field
        def create_order(self, input: CreateOrderInput) -> str:
            return f"{input.id} {input.number} {input.reference}"

    schema = strawberry.Schema(query=Query)

    # fields whose default is applied by pydantic can be omitted
    assert _input_sdl(schema, "CreateOrderInput") == snapshot("""\
input CreateOrderInput {
  id: UUID
  number: Int
  reference: String
}\
""")

    first = schema.execute_sync("{ createOrder(input: {}) }")
    second = schema.execute_sync("{ createOrder(input: {}) }")

    assert not first.errors
    assert not second.errors

    first_id, first_number, first_reference = first.data["createOrder"].split()
    second_id, second_number, second_reference = second.data["createOrder"].split()

    assert first_id != second_id
    assert (first_number, second_number) == ("1", "2")
    assert (first_reference, second_reference) == (first_id, second_id)


def test_model_defaults_are_published():
    @strawberry.pydantic.input
    class AddressInput(pydantic.BaseModel):
        city: str

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        address: AddressInput = AddressInput(city="Rome")

    @strawberry.type
    class Query:
        @strawberry.field
        def create_user(self, input: CreateUserInput) -> str:
            return input.address.city

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "CreateUserInput") == snapshot("""\
input CreateUserInput {
  address: AddressInput! = { city: "Rome" }
}\
""")

    result = schema.execute_sync("{ createUser(input: {}) }")

    assert not result.errors
    assert result.data == {"createUser": "Rome"}


def test_model_argument_defaults_only_include_the_fields_that_were_set():
    @strawberry.pydantic.input
    class UpdateUserInput(pydantic.BaseModel):
        name: str | None = None
        email: str | None = None
        bio: str | None = None
        role: str = "user"

    @strawberry.type
    class Query:
        @strawberry.field
        def update_user(
            self, input: UpdateUserInput = UpdateUserInput(name="Ada", bio=None)
        ) -> str:
            return repr(input.model_dump(exclude_unset=True))

    schema = strawberry.Schema(query=Query)

    assert (
        'updateUser(input: UpdateUserInput! = { name: "Ada", bio: null }): String!'
        in str(schema)
    )

    # The explicitly constructed argument default is validated again.
    result = schema.execute_sync("{ updateUser }")

    assert not result.errors
    assert result.data == {"updateUser": "{'name': 'Ada', 'bio': None}"}


def test_nested_model_argument_defaults_only_include_the_fields_that_were_set():
    @strawberry.pydantic.input
    class PaginationInput(pydantic.BaseModel):
        page_size: int | None = None
        cursor: str | None = None

    @strawberry.pydantic.input
    class SearchInput(pydantic.BaseModel):
        query: str
        pagination: PaginationInput | None = None

    @strawberry.type
    class Query:
        @strawberry.field
        def search(
            self,
            input: SearchInput = SearchInput(
                query="jam", pagination=PaginationInput(page_size=5)
            ),
        ) -> str:
            return repr(input.model_dump(exclude_unset=True))

    schema = strawberry.Schema(query=Query)

    assert (
        'search(input: SearchInput! = { query: "jam", pagination: { pageSize: 5 } }): '
        "String!" in str(schema)
    )

    result = schema.execute_sync("{ search }")

    assert not result.errors
    assert result.data == {"search": "{'query': 'jam', 'pagination': {'page_size': 5}}"}


def test_null_for_a_field_with_an_unpublished_default_is_validated_by_pydantic():
    @strawberry.pydantic.input
    class CreateOrderInput(pydantic.BaseModel):
        id: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)

    @strawberry.type
    class Query:
        @strawberry.field
        def create_order(self, input: CreateOrderInput) -> str:
            return str(input.id)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ createOrder(input: {id: null}) }")

    assert result.errors
    assert result.errors[0].message.startswith("Invalid input: input.id:")


def test_omitted_nullable_fields_without_a_default_are_none():
    @strawberry.pydantic.input
    class AddressInput(pydantic.BaseModel):
        city: str
        line2: str | None

    @strawberry.pydantic.input
    class ProfileInput(pydantic.BaseModel):
        nickname: str | None
        bio: str | None = None
        address: AddressInput | None = None

    @strawberry.type
    class Query:
        @strawberry.field
        def profile(self, input: ProfileInput) -> str:
            return repr(input.model_dump(exclude_unset=True))

    schema = strawberry.Schema(query=Query)

    # nullable input fields are optional for clients, as GraphQL requires
    assert _input_sdl(schema, "ProfileInput") == snapshot("""\
input ProfileInput {
  nickname: String
  bio: String = null
  address: AddressInput = null
}\
""")

    # Required nullable fields become None; GraphQL supplies explicit defaults.
    result = schema.execute_sync('{ profile(input: {address: {city: "Rome"}}) }')

    assert not result.errors
    assert result.data == {
        "profile": (
            "{'nickname': None, 'bio': None, "
            "'address': {'city': 'Rome', 'line2': None}}"
        )
    }

    result = schema.execute_sync('{ profile(input: {nickname: "ada"}) }')

    assert not result.errors
    assert result.data == {
        "profile": "{'nickname': 'ada', 'bio': None, 'address': None}"
    }


def test_unset_defaults_are_not_published():
    @strawberry.pydantic.input
    class FilterInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

        name: str | None = strawberry.UNSET  # type: ignore[assignment]

    @strawberry.type
    class Query:
        @strawberry.field
        def filter(self, input: FilterInput) -> str:
            return repr(input.model_fields_set)

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "FilterInput") == snapshot("""\
input FilterInput {
  name: String
}\
""")


def test_output_types_keep_their_nullability():
    @strawberry.pydantic.type
    class Order(pydantic.BaseModel):
        id: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)
        color: Color = Color.RED

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self) -> Order:
            return Order()

    schema = strawberry.Schema(query=Query)

    assert "id: UUID!" in str(schema)
    assert "color: Color!" in str(schema)


@pytest.mark.parametrize(
    ("annotation", "default", "message"),
    [
        (int, 5 * 1024**3, "Int cannot represent non 32-bit signed integer value"),
        (float, float("inf"), "Float cannot represent non numeric value"),
        (str, "abc", "Int cannot represent non-integer value"),
    ],
)
def test_invalid_defaults_are_not_silently_hidden(annotation, default, message):
    from graphql import GraphQLError

    @strawberry.pydantic.input
    class EventInput(pydantic.BaseModel):
        value: Annotated[
            annotation,
            strawberry.field(graphql_type=float if annotation is float else int),
        ] = default

    @strawberry.type
    class Query:
        @strawberry.field
        def event(self, input: EventInput) -> bool:
            return True

    schema = strawberry.Schema(query=Query)

    with pytest.raises(GraphQLError, match=message):
        str(schema)


def test_typed_constants_are_published():
    @strawberry.pydantic.input
    class PaymentInput(pydantic.BaseModel):
        amount: decimal.Decimal = decimal.Decimal("1.50")
        due: dt.date = dt.date(2020, 1, 2)
        account: strawberry.ID = strawberry.ID("main")
        enabled: bool | None = False

    @strawberry.type
    class Query:
        @strawberry.field
        def pay(self, input: PaymentInput) -> str:
            return repr(sorted(input.model_fields_set))

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "PaymentInput") == snapshot("""\
input PaymentInput {
  amount: Decimal! = "1.50"
  due: Date! = "2020-01-02"
  account: ID! = "main"
  enabled: Boolean = false
}\
""")


def test_tuple_defaults_are_published():
    @strawberry.pydantic.input
    class ProductInput(pydantic.BaseModel):
        # in strict mode, pydantic doesn't accept the lists of GraphQL for tuples
        model_config = pydantic.ConfigDict(strict=True)

        labels: tuple[str, ...] = ("sale",)

    @strawberry.type
    class Query:
        @strawberry.field
        def product(self, input: ProductInput) -> str:
            return repr(input.labels)

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "ProductInput") == snapshot("""\
input ProductInput {
  labels: [String!]! = ["sale"]
}\
""")

    result = schema.execute_sync("{ product(input: {}) }")

    assert not result.errors
    assert result.data == {"product": "('sale',)"}


def test_graphql_type_overrides_follow_the_same_rules():
    @strawberry.pydantic.input
    class SettingsInput(pydantic.BaseModel):
        extra: Annotated[dict[str, Any], strawberry.field(graphql_type=JSON)] = (
            pydantic.Field(default_factory=dict)
        )
        limit: Annotated[int, strawberry.field(graphql_type=int)] = 10
        # the type of the items of bare lists isn't known
        tags: Annotated[
            typing.List,  # noqa: UP006
            strawberry.field(graphql_type=list[str]),
        ] = ["new"]

    @strawberry.type
    class Query:
        @strawberry.field
        def settings(self, input: SettingsInput) -> str:
            return repr(input.model_dump(exclude_unset=True))

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "SettingsInput") == snapshot("""\
input SettingsInput {
  extra: JSON
  limit: Int! = 10
  tags: [String!]! = ["new"]
}\
""")

    result = schema.execute_sync("{ settings(input: {}) }")

    assert not result.errors
    assert result.data == {"settings": "{'limit': 10, 'tags': ['new']}"}


def test_published_defaults_are_kept_when_fields_are_copied():
    # `Self` makes Strawberry copy the fields when the type is created
    @strawberry.pydantic.input
    class NodeInput(pydantic.BaseModel):
        name: str = "root"
        children: list[Self] = []

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self, input: NodeInput) -> str:
            return input.name

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "NodeInput") == snapshot("""\
input NodeInput {
  name: String! = "root"
  children: [NodeInput!]! = []
}\
""")


def test_fields_from_strawberry_input_bases_follow_the_same_rules():
    @strawberry.input
    class Pagination:
        cursor: str | None = None

    @strawberry.pydantic.input
    class SearchInput(pydantic.BaseModel, Pagination):
        query: str | None = None

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, input: SearchInput) -> str:
            return repr(sorted(input.model_fields_set))

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "SearchInput") == snapshot("""\
input SearchInput {
  cursor: String = null
  query: String = null
}\
""")

    result = schema.execute_sync('{ search(input: {query: "jam"}) }')

    assert not result.errors
    assert result.data == {"search": "['cursor', 'query']"}


@pytest.mark.raises_strawberry_exception(
    UnsupportedInheritedFieldError,
    match=(
        r"Pydantic input `SearchInput` can't use the default factory of field "
        r"`tags`, inherited from `Pagination`"
    ),
)
def test_default_factories_inherited_from_strawberry_input_bases_raise_an_error():
    @strawberry.input
    class Pagination:
        # the dataclass removes the factory from the class, so pydantic would
        # require the field, and get `None` for it when a client omits it
        tags: list[str] | None = strawberry.field(default_factory=lambda: ["all"])

    @strawberry.pydantic.input
    class SearchInput(pydantic.BaseModel, Pagination):
        query: str | None = None


@pytest.mark.raises_strawberry_exception(
    MaybeFieldError,
    match=(
        r"Field `name` on pydantic input `UpdateUserInput` can't use "
        r"`strawberry\.Maybe`"
    ),
)
def test_maybe_fields_on_inputs_raise_an_error():
    @strawberry.pydantic.input
    class UpdateUserInput(pydantic.BaseModel):
        # without it pydantic itself rejects `strawberry.Maybe`
        model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

        name: strawberry.Maybe[str] = None
