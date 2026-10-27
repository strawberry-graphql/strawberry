import datetime as dt
import io
from typing import Annotated, Generic, NewType, TypeVar

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.file_uploads import Upload
from strawberry.scalars import JSON
from strawberry.schema.config import StrawberryConfig

UserId = NewType("UserId", int)
Money = NewType("Money", str)


def test_id_fields():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: strawberry.ID
        friend_ids: list[strawberry.ID]
        manager_id: strawberry.ID | None = None

    @strawberry.pydantic.input
    class UserFilter(pydantic.BaseModel):
        id: strawberry.ID

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, filter: UserFilter) -> User:
            return User(id=filter.id, friend_ids=[strawberry.ID("2")])

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Query {
  user(filter: UserFilter!): User!
}

type User {
  id: ID!
  friendIds: [ID!]!
  managerId: ID
}

input UserFilter {
  id: ID!
}\
""")

    # ID accepts integer literals, which String doesn't
    result = schema.execute_sync("{ user(filter: {id: 1}) { id friendIds managerId } }")

    assert not result.errors
    assert result.data == {"user": {"id": "1", "friendIds": ["2"], "managerId": None}}


def test_json_fields():
    @strawberry.pydantic.type
    class Settings(pydantic.BaseModel):
        values: JSON

    @strawberry.pydantic.input
    class SettingsInput(pydantic.BaseModel):
        values: JSON

    @strawberry.type
    class Query:
        @strawberry.field
        def settings(self, input: SettingsInput) -> Settings:
            return Settings(values=input.values)

    schema = strawberry.Schema(query=Query)

    assert "values: JSON!" in str(schema)

    result = schema.execute_sync(
        '{ settings(input: {values: {theme: "dark", fontSize: 12}}) { values } }'
    )

    assert not result.errors
    assert result.data == {"settings": {"values": {"theme": "dark", "fontSize": 12}}}


def test_upload_fields_on_inputs():
    # Uploads are the integration's file objects, not `bytes`, so pydantic
    # validates them as the file type while GraphQL uses the Upload scalar
    @strawberry.pydantic.input
    class CreatePostInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

        title: str
        image: Annotated[io.BytesIO, strawberry.field(graphql_type=Upload)]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_post(self, input: CreatePostInput) -> str:
            return input.image.read().decode()

    @strawberry.type
    class Query:
        hello: str = "world"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    assert "image: Upload!" in str(schema)

    result = schema.execute_sync(
        'mutation ($image: Upload!) { createPost(input: {title: "Hi", image: $image}) }',
        variable_values={"image": io.BytesIO(b"image content")},
    )

    assert not result.errors
    assert result.data == {"createPost": "image content"}


@pytest.mark.parametrize(
    "custom_validator",
    [False, True],
)
def test_upload_validation_belongs_to_pydantic(custom_validator):
    annotation = (
        Annotated[Upload, pydantic.PlainValidator(lambda value: value)]
        if custom_validator
        else Upload
    )

    @strawberry.pydantic.input
    class CreatePostInput(pydantic.BaseModel):
        images: list[annotation]

    @strawberry.type
    class Query:
        @strawberry.field
        def read(self, data: CreatePostInput) -> str:
            return data.images[0].read().decode()

    result = strawberry.Schema(query=Query).execute_sync(
        "query($data: CreatePostInput!) { read(data: $data) }",
        variable_values={"data": {"images": [io.BytesIO(b"image content")]}},
    )
    if custom_validator:
        assert not result.errors
        assert result.data == {"read": "image content"}
    else:
        assert result.errors
        assert (
            result.errors[0].extensions["validationErrors"][0]["type"] == "bytes_type"
        )


@pytest.mark.parametrize("annotated", [False, True])
def test_custom_scalar_new_types(annotated):
    definition = strawberry.scalar(
        name="Money",
        serialize=lambda value: f"{value} EUR",
        parse_value=lambda value: value.removesuffix(" EUR"),
    )
    MoneyType = Annotated[Money, definition] if annotated else Money

    @strawberry.pydantic.type
    class Product(pydantic.BaseModel):
        price: MoneyType

    @strawberry.pydantic.input
    class ProductInput(pydantic.BaseModel):
        price: MoneyType

    @strawberry.type
    class Query:
        @strawberry.field
        def product(self, input: ProductInput) -> Product:
            return Product(price=input.price)

    schema = strawberry.Schema(
        query=Query,
        scalar_map={} if annotated else {Money: definition},
    )

    assert "price: Money!" in str(schema)

    result = schema.execute_sync(
        "query ($price: Money!) { product(input: {price: $price}) { price } }",
        variable_values={"price": "10 EUR"},
    )

    assert not result.errors
    assert result.data == {"product": {"price": "10 EUR"}}


def test_unregistered_new_types_are_rejected_like_strawberry_types():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: UserId

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(id=UserId(1))

    with pytest.raises(
        TypeError,
        match=r"User fields cannot be resolved\. Unexpected type '.*\.UserId'",
    ):
        strawberry.Schema(query=Query)


def test_new_types_can_be_exposed_as_their_base_type():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: Annotated[UserId, strawberry.field(graphql_type=int)]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(id=UserId(1))

    schema = strawberry.Schema(query=Query)

    assert "id: Int!" in str(schema)

    result = schema.execute_sync("{ user { id } }")

    assert not result.errors
    assert result.data == {"user": {"id": 1}}


def test_constrained_date_types():
    @strawberry.pydantic.type
    class Event(pydantic.BaseModel):
        created_at: pydantic.AwareDatetime
        local_time: pydantic.NaiveDatetime
        born_on: pydantic.PastDate
        due_on: pydantic.FutureDate

    @strawberry.pydantic.input
    class EventInput(pydantic.BaseModel):
        due_on: pydantic.FutureDate

    @strawberry.type
    class Query:
        @strawberry.field
        def event(self, input: EventInput) -> Event:
            return Event(
                created_at=dt.datetime(2020, 1, 1, tzinfo=dt.UTC),
                local_time=dt.datetime(2020, 1, 1),
                born_on=dt.date(2000, 1, 1),
                due_on=input.due_on,
            )

    schema = strawberry.Schema(query=Query)

    sdl = str(schema)

    assert "createdAt: DateTime!" in sdl
    assert "localTime: DateTime!" in sdl
    assert "bornOn: Date!" in sdl
    assert "dueOn: Date!" in sdl

    result = schema.execute_sync(
        '{ event(input: {dueOn: "2999-01-01"}) { createdAt dueOn } }'
    )

    assert not result.errors
    assert result.data == {
        "event": {"createdAt": "2020-01-01T00:00:00+00:00", "dueOn": "2999-01-01"}
    }

    # pydantic still validates the constraint
    result = schema.execute_sync('{ event(input: {dueOn: "2000-01-01"}) { dueOn } }')

    assert result.errors
    assert result.errors[0].extensions["validationErrors"][0]["type"] == "date_future"


class CompanyUrl(pydantic.AnyHttpUrl):
    pass


@pytest.mark.parametrize(
    ("annotation", "value"),
    [
        (pydantic.AnyUrl, "https://example.com/docs"),
        (pydantic.AnyHttpUrl, "https://example.com/docs"),
        (pydantic.HttpUrl, "https://example.com/docs"),
        (pydantic.FileUrl, "file:///tmp/report.txt"),
        (pydantic.FtpUrl, "ftp://example.com/report.txt"),
        (pydantic.WebsocketUrl, "wss://example.com/live"),
        (pydantic.AnyWebsocketUrl, "ws://example.com/live"),
        (pydantic.PostgresDsn, "postgres://ada:secret@db1:5432,db2:5432/app"),
        (pydantic.CockroachDsn, "cockroachdb://ada@localhost:26257/app"),
        (pydantic.AmqpDsn, "amqp://localhost:5672"),
        (pydantic.RedisDsn, "redis://localhost:6379/0"),
        (pydantic.MongoDsn, "mongodb://db1:27017,db2:27017/app"),
        (pydantic.KafkaDsn, "kafka://localhost:9092"),
        (pydantic.NatsDsn, "nats://localhost:4222"),
        (pydantic.MySQLDsn, "mysql://ada@localhost:3306/app"),
        (pydantic.MariaDBDsn, "mariadb://ada@localhost:3306/app"),
        (pydantic.ClickHouseDsn, "clickhouse+native://localhost:9000/app"),
        (pydantic.SnowflakeDsn, "snowflake://ada:secret@account/app"),
        (CompanyUrl, "https://example.com/docs"),
        (pydantic.EmailStr, "ada@example.com"),
        (pydantic.NameEmail, "Ada Lovelace <ada@example.com>"),
        (pydantic.IPvAnyAddress, "192.168.0.1"),
        (pydantic.IPvAnyInterface, "192.168.0.1/24"),
        (pydantic.IPvAnyNetwork, "2001:db8::/32"),
    ],
)
def test_network_types_are_strings(annotation: type, value: str):
    @strawberry.pydantic.type
    class Resource(pydantic.BaseModel):
        value: annotation  # type: ignore[valid-type]

    @strawberry.pydantic.input
    class ResourceInput(pydantic.BaseModel):
        value: annotation  # type: ignore[valid-type]

    # e.g. a `HttpUrl` instance, or an `IPv4Address` for `IPvAnyAddress`
    validated = pydantic.TypeAdapter(annotation).validate_python(value)

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, resource: ResourceInput) -> Resource:
            assert resource.value == validated

            return Resource(value=resource.value)

    schema = strawberry.Schema(query=Query)

    assert "value: String!" in str(schema)

    result = schema.execute_sync(
        "query ($value: String!) { echo(resource: { value: $value }) { value } }",
        variable_values={"value": value},
    )

    assert not result.errors
    assert result.data == {"echo": {"value": str(validated)}}


def test_secret_str_fields_expose_the_masked_value():
    @strawberry.pydantic.type
    class Login(pydantic.BaseModel):
        password: pydantic.SecretStr

    @strawberry.type
    class Query:
        @strawberry.field
        def login(self) -> Login:
            return Login(password=pydantic.SecretStr("hunter2"))

    schema = strawberry.Schema(query=Query)

    assert "password: String!" in str(schema)

    result = schema.execute_sync("{ login { password } }")

    assert not result.errors
    assert result.data == {"login": {"password": "**********"}}


def test_private_secret_fields():
    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        username: str
        password: strawberry.Private[pydantic.SecretStr]
        signing_key: strawberry.Private[pydantic.SecretBytes]

        @strawberry.pydantic.field
        def has_signing_key(self) -> bool:
            return bool(self.signing_key.get_secret_value())

    @strawberry.type
    class Query:
        @strawberry.field
        def account(self) -> Account:
            return Account(username="ada", password="hunter2", signing_key=b"key")

    schema = strawberry.Schema(query=Query)

    assert "password" not in str(schema)
    assert "signingKey" not in str(schema)

    result = schema.execute_sync("{ account { username hasSigningKey } }")

    assert not result.errors
    assert result.data == {"account": {"username": "ada", "hasSigningKey": True}}


def test_secret_bytes_fields_are_not_supported():
    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        signing_key: pydantic.SecretBytes

    @strawberry.type
    class Query:
        account: Account

    with pytest.raises(TypeError, match=r"Unexpected type .*SecretBytes"):
        strawberry.Schema(query=Query)


class CustomUrl(pydantic.HttpUrl):
    pass


@pytest.mark.parametrize(
    ("annotation", "value"),
    [
        (pydantic.EmailStr, "ada@example.com"),
        (pydantic.HttpUrl, "https://example.com/"),
        (CustomUrl, "https://example.com/"),
        (pydantic.AwareDatetime, "2024-02-03 04:05:00+00:00"),
        (pydantic.PastDate, "2024-02-03"),
    ],
)
def test_explicit_scalar_maps_override_pydantic_fallbacks(annotation, value):
    T = TypeVar("T")

    @strawberry.pydantic.input
    class Input(pydantic.BaseModel):
        values: list[annotation | None]

    @strawberry.pydantic.type
    class Output(pydantic.BaseModel, Generic[T]):
        values: list[T | None]

        @pydantic.computed_field
        @property
        def first(self) -> T | None:
            return self.values[0]

    @strawberry.pydantic.type
    class SpecializedOutput(Output[annotation]):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, data: Input) -> SpecializedOutput:
            return SpecializedOutput(values=data.values)

    ordinary_sdl = str(strawberry.Schema(query=Query))
    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            scalar_map={
                annotation: strawberry.scalar(
                    name="Encoded",
                    serialize=lambda value: f"encoded:{value}",
                    parse_value=lambda value: value.removeprefix("encoded:"),
                )
            }
        ),
    )
    assert "values: [Encoded]!" in str(schema)
    result = schema.execute_sync(
        "query($data: Input!) { echo(data: $data) { values first } }",
        variable_values={"data": {"values": [f"encoded:{value}", None]}},
    )
    assert not result.errors
    assert result.data == {
        "echo": {"values": [f"encoded:{value}", None], "first": f"encoded:{value}"}
    }
    assert str(strawberry.Schema(query=Query)) == ordinary_sdl


@pytest.mark.parametrize("return_instance", [False, True])
def test_undecorated_models_can_be_scalar_map_keys(return_instance):
    class Token(pydantic.BaseModel):
        value: str

    @strawberry.pydantic.input
    class Input(pydantic.BaseModel):
        tokens: list[Token | None]

    @strawberry.pydantic.type
    class Output(pydantic.BaseModel):
        tokens: list[Token | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, data: Input) -> Output:
            return Output(tokens=data.tokens)

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            scalar_map={
                Token: strawberry.scalar(
                    name="Token",
                    serialize=lambda token: token.value,
                    parse_value=lambda value: (
                        Token(value=value) if return_instance else {"value": value}
                    ),
                )
            }
        ),
    )
    result = schema.execute_sync(
        '{ echo(data: {tokens: ["opaque", null]}) { tokens } }'
    )
    assert not result.errors
    assert result.data == {"echo": {"tokens": ["opaque", None]}}
