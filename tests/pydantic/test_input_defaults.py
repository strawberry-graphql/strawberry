import datetime
import decimal
import uuid
from enum import Enum
from typing import Annotated, Any
from typing_extensions import Self

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.pydantic.exceptions import MaybeFieldError
from strawberry.scalars import JSON


class Color(Enum):
    RED = "red"
    BLUE = "blue"


def _input_sdl(schema: strawberry.Schema, name: str) -> str:
    sdl = str(schema)
    start = sdl.index(f"input {name} ")

    return sdl[start : sdl.index("}", start) + 1]


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
}\
""")

    result = schema.execute_sync("{ search(input: {}) }")

    assert not result.errors
    assert result.data == {
        "search": (
            '{"query":"","page_size":20,"min_score":0.5,"exact":false,'
            '"size":"small","tags":["new"]}'
        )
    }


def test_omitted_fields_with_none_defaults_are_not_set():
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
  name: String
  bio: String
}\
""")

    # omitted fields aren't set, so PATCH-style updates don't overwrite them
    result = schema.execute_sync('{ updateUser(input: {bio: "Hi"}) }')

    assert not result.errors
    assert result.data == {"updateUser": "{'bio': 'Hi'}"}

    # an explicit null is set, so it can be used to clear a value
    result = schema.execute_sync("{ updateUser(input: {name: null}) }")

    assert not result.errors
    assert result.data == {"updateUser": "{'name': None}"}


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

    # factories are applied by pydantic, not when the class is decorated
    assert calls == 0

    @strawberry.type
    class Query:
        @strawberry.field
        def create_order(self, input: CreateOrderInput) -> str:
            return f"{input.id} {input.number}"

    schema = strawberry.Schema(query=Query)

    # fields whose default is applied by pydantic can be omitted
    assert _input_sdl(schema, "CreateOrderInput") == snapshot("""\
input CreateOrderInput {
  id: UUID
  number: Int
}\
""")

    first = schema.execute_sync("{ createOrder(input: {}) }")
    second = schema.execute_sync("{ createOrder(input: {}) }")

    assert not first.errors
    assert not second.errors

    first_id, first_number = first.data["createOrder"].split()
    second_id, second_number = second.data["createOrder"].split()

    assert first_id != second_id
    assert (first_number, second_number) == ("1", "2")


def test_model_defaults_are_applied_by_pydantic():
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
  address: AddressInput
}\
""")

    result = schema.execute_sync("{ createUser(input: {}) }")

    assert not result.errors
    assert result.data == {"createUser": "Rome"}


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


def test_optional_fields_without_a_default_are_required_by_pydantic():
    @strawberry.pydantic.input
    class ProfileInput(pydantic.BaseModel):
        nickname: str | None

    @strawberry.type
    class Query:
        @strawberry.field
        def profile(self, input: ProfileInput) -> str:
            return repr(input.nickname)

    schema = strawberry.Schema(query=Query)

    # GraphQL can't express required nullable input fields
    assert _input_sdl(schema, "ProfileInput") == snapshot("""\
input ProfileInput {
  nickname: String
}\
""")

    result = schema.execute_sync("{ profile(input: {nickname: null}) }")

    assert not result.errors
    assert result.data == {"profile": "None"}

    result = schema.execute_sync("{ profile(input: {}) }")

    assert result.errors
    assert "Field required" in result.errors[0].message


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


def test_constants_of_other_types_are_applied_by_pydantic():
    @strawberry.pydantic.input
    class EventInput(pydantic.BaseModel):
        # GraphQL can't represent these values
        max_bytes: int = 5 * 1024**3
        ratio: float = float("inf")
        # pydantic converts these values to the field type
        since: datetime.date = "2020-01-02"  # type: ignore[assignment]
        color: Color = "red"  # type: ignore[assignment]

    @strawberry.type
    class Query:
        @strawberry.field
        def event(self, input: EventInput) -> bool:
            # the defaults are the ones pydantic applies
            return input == EventInput()

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "EventInput") == snapshot("""\
input EventInput {
  maxBytes: Int
  ratio: Float
  since: Date
  color: Color
}\
""")

    result = schema.execute_sync("{ event(input: {}) }")

    assert not result.errors
    assert result.data == {"event": True}


def test_typed_constants_are_published():
    @strawberry.pydantic.input
    class PaymentInput(pydantic.BaseModel):
        amount: decimal.Decimal = decimal.Decimal("1.50")
        due: datetime.date = datetime.date(2020, 1, 2)
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


def test_graphql_type_overrides_follow_the_same_rules():
    @strawberry.pydantic.input
    class SettingsInput(pydantic.BaseModel):
        extra: Annotated[dict[str, Any], strawberry.field(graphql_type=JSON)] = (
            pydantic.Field(default_factory=dict)
        )
        limit: Annotated[int, strawberry.field(graphql_type=int)] = 10

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
}\
""")

    result = schema.execute_sync("{ settings(input: {}) }")

    assert not result.errors
    assert result.data == {"settings": "{'limit': 10}"}


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
  cursor: String
  query: String
}\
""")

    result = schema.execute_sync('{ search(input: {query: "jam"}) }')

    assert not result.errors
    assert result.data == {"search": "['query']"}


def test_maybe_fields_on_inputs_raise_an_error():
    with pytest.raises(
        MaybeFieldError,
        match=(
            r"Field `name` on pydantic input `UpdateUserInput` can't use "
            r"`strawberry\.Maybe`"
        ),
    ):

        @strawberry.pydantic.input
        class UpdateUserInput(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

            name: strawberry.Maybe[str] = None


def test_constant_defaults_of_constrained_date_fields_are_published():
    @strawberry.pydantic.input
    class EventInput(pydantic.BaseModel):
        due_on: pydantic.FutureDate = datetime.date(2999, 1, 1)

    @strawberry.type
    class Query:
        @strawberry.field
        def event(self, input: EventInput) -> str:
            return input.due_on.isoformat()

    schema = strawberry.Schema(query=Query)

    assert _input_sdl(schema, "EventInput") == snapshot("""\
input EventInput {
  dueOn: Date! = "2999-01-01"
}\
""")
