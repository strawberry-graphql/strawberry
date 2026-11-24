from datetime import datetime
from typing import Annotated, Any, Generic, TypeVar

import pydantic
import pytest
from pydantic import PlainSerializer, WrapSerializer
from pydantic.fields import FieldInfo

import strawberry
from strawberry.pydantic.exceptions import IgnoredSerializerError

# `Field(exclude_if=...)` is new in pydantic 2.12
HAS_EXCLUDE_IF = hasattr(FieldInfo(), "exclude_if")


def _execute(type_: type, value: object, query: str) -> Any:
    @strawberry.type
    class Query:
        @strawberry.field
        def item(self) -> type_:  # type: ignore[valid-type]
            return value

    result = strawberry.Schema(query=Query).execute_sync(query)

    assert not result.errors

    return result.data


@pytest.mark.raises_strawberry_exception(
    IgnoredSerializerError,
    match=(
        "Pydantic type `Event` customizes how `starts_at` is serialized, which "
        "GraphQL doesn't apply$"
    ),
)
def test_field_serializers_raise_an_error():
    @strawberry.pydantic.type
    class Event(pydantic.BaseModel):
        name: str
        starts_at: datetime

        @pydantic.field_serializer("starts_at")
        def as_date(self, value: datetime) -> str:
            return value.strftime("%Y-%m-%d")


@pytest.mark.raises_strawberry_exception(
    IgnoredSerializerError,
    match=("Pydantic type `User` has a model serializer, which GraphQL doesn't apply$"),
)
def test_model_serializers_raise_an_error():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        email: str

        @pydantic.model_serializer
        def public(self) -> dict[str, str]:
            return {"name": self.name}


@pytest.mark.parametrize(
    "serializer",
    [
        pytest.param(PlainSerializer(lambda value: "***"), id="plain"),
        pytest.param(WrapSerializer(lambda value, handler: "***"), id="wrap"),
    ],
)
def test_annotated_serializers_raise_an_error(serializer: object):
    with pytest.raises(IgnoredSerializerError) as exc_info:

        @strawberry.pydantic.type
        class User(pydantic.BaseModel):
            name: str
            email: Annotated[str, serializer]
            # nested in the type, they serialize the items
            phones: list[Annotated[str, serializer]] = []

            @pydantic.computed_field
            @property
            def secret(self) -> Annotated[str, serializer]:
                return "sensitive"

            @pydantic.computed_field
            @property
            def secrets(self) -> list[Annotated[str, serializer]]:
                return ["sensitive"]

    assert str(exc_info.value) == (
        "Pydantic type `User` customizes how `email`, `phones`, `secret` and "
        "`secrets` are serialized, which GraphQL doesn't apply"
    )


def test_serializers_for_all_fields_raise_an_error():
    with pytest.raises(IgnoredSerializerError) as exc_info:

        @strawberry.pydantic.type
        class User(pydantic.BaseModel):
            name: str
            email: str
            password: strawberry.Private[str]

            @pydantic.field_serializer("*")
            def strip(self, value: Any) -> Any:
                return value

    # only the fields of the GraphQL type
    assert exc_info.value.field_names == ["name", "email"]


@pytest.mark.skipif(not HAS_EXCLUDE_IF, reason="needs pydantic 2.12")
def test_exclude_if_raises_an_error():
    with pytest.raises(IgnoredSerializerError) as exc_info:

        @strawberry.pydantic.type
        class User(pydantic.BaseModel):
            name: str
            nickname: str | None = pydantic.Field(
                default=None, exclude_if=lambda value: value is None
            )

    assert exc_info.value.field_names == ["nickname"]


def test_serializers_of_base_models_and_computed_fields_raise_an_error():
    class Base(pydantic.BaseModel):
        first_name: str
        last_name: str

        @pydantic.computed_field
        @property
        def full_name(self) -> str:
            return f"{self.first_name} {self.last_name}"

        @pydantic.field_serializer("full_name")
        def upper(self, value: str) -> str:
            return value.upper()

    with pytest.raises(IgnoredSerializerError) as exc_info:

        @strawberry.pydantic.type
        class User(Base):
            pass

    assert exc_info.value.field_names == ["full_name"]


def test_serializers_of_fields_that_arent_exposed_are_allowed():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        password: strawberry.Private[str]
        api_key: str = pydantic.Field(exclude=True)

        @pydantic.field_serializer("password", "api_key")
        def hide(self, value: str) -> str:
            return "***"

        @pydantic.computed_field
        @property
        def secret(
            self,
        ) -> strawberry.Private[Annotated[str, PlainSerializer(lambda value: "***")]]:
            return "sensitive"

    data = _execute(
        User, User(name="Ada", password="p", api_key="k"), "{ item { name } }"
    )

    assert data == {"item": {"name": "Ada"}}


def test_inputs_can_have_serializers():
    @strawberry.pydantic.input
    class EventInput(pydantic.BaseModel):
        starts_at: datetime

        @pydantic.field_serializer("starts_at")
        def as_date(self, value: datetime) -> str:
            return value.strftime("%Y-%m-%d")

    @strawberry.type
    class Query:
        @strawberry.field
        def event(self, input: EventInput) -> datetime:
            return input.starts_at

    result = strawberry.Schema(query=Query).execute_sync(
        '{ event(input: {startsAt: "2026-10-17T09:30:00"}) }'
    )

    assert not result.errors
    assert result.data == {"event": "2026-10-17T09:30:00"}


def test_interfaces_raise_an_error():
    with pytest.raises(IgnoredSerializerError) as exc_info:

        @strawberry.pydantic.interface
        class Node(pydantic.BaseModel):
            id: int

            @pydantic.field_serializer("id")
            def as_string(self, value: int) -> str:
                return str(value)

    assert str(exc_info.value) == (
        "Pydantic interface `Node` customizes how `id` is serialized, which "
        "GraphQL doesn't apply"
    )


def test_parametrized_generic_models_reject_serializers():
    T = TypeVar("T")

    @strawberry.pydantic.type
    class Page(pydantic.BaseModel, Generic[T]):
        items: list[T]

    Secret = Annotated[str, PlainSerializer(lambda value: "***")]

    with pytest.raises(IgnoredSerializerError) as exc_info:
        strawberry.Schema(query=Page[Secret])

    assert exc_info.value.field_names == ["items"]


def test_error_message_and_suggestion():
    rich_console = pytest.importorskip("rich.console")

    with pytest.raises(IgnoredSerializerError) as exc_info:

        @strawberry.pydantic.type
        class Event(pydantic.BaseModel):
            starts_at: datetime

            @pydantic.field_serializer("starts_at")
            def as_date(self, value: datetime) -> str:
                return value.strftime("%Y-%m-%d")

    assert exc_info.value.suggestion == (
        "GraphQL resolves fields from the model's attributes, not from "
        "`model_dump()`, so Pydantic's serializers would silently be ignored. To "
        "change a value in GraphQL, use a field with a resolver or a custom "
        "scalar, and to hide it, `strawberry.Private` or `Field(exclude=True)`."
    )

    console = rich_console.Console(width=200, color_system=None)

    with console.capture() as capture:
        console.print(exc_info.value)

    # points at the serializer
    assert "def as_date(self, value: datetime) -> str:" in capture.get()
