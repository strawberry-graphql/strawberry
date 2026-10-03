import functools
from collections.abc import Callable
from typing import Any, Generic, TypeVar

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.exceptions import MissingReturnAnnotationError
from strawberry.pydantic.exceptions import (
    ResolverAlreadyUsedError,
    ResolverFieldOnInputError,
    ResolverFieldOverridesModelFieldError,
)
from strawberry.scalars import JSON
from strawberry.types.base import get_object_definition
from strawberry.types.field import StrawberryField

T = TypeVar("T")


class IsAdmin(strawberry.BasePermission):
    message = "Admins only"

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return info.context["admin"]


@strawberry.pydantic.type
class Post(pydantic.BaseModel):
    title: str


@strawberry.pydantic.type
class Book(pydantic.BaseModel):
    title: str


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field
    def greeting(self, punctuation: str = "!") -> str:
        return f"Hi {self.name}{punctuation}"

    @strawberry.pydantic.field
    async def posts(self, info: strawberry.Info, first: int = 10) -> list["Post"]:
        return [Post(title=title) for title in info.context["posts"][:first]]

    @strawberry.pydantic.field(
        name="contact",
        description="How to reach the user",
        deprecation_reason="Use email",
        permission_classes=[IsAdmin],
    )
    def contact_details(self) -> str:
        return "ada@example.com"

    @strawberry.pydantic.field(graphql_type=JSON)
    def settings(self) -> dict[str, Any]:
        return {"theme": "dark"}


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Ada")


schema = strawberry.Schema(query=Query)


def test_schema():
    sdl = str(schema)
    start = sdl.index("type User ")

    assert sdl[start : sdl.index("}", start) + 1] == snapshot('''\
type User {
  name: String!
  greeting(punctuation: String! = "!"): String!
  posts(first: Int! = 10): [Post!]!

  """How to reach the user"""
  contact: String! @deprecated(reason: "Use email")
  settings: JSON!
}\
''')


async def test_resolver_fields():
    result = await schema.execute(
        '{ user { name greeting(punctuation: "?") posts(first: 1) { title } '
        "contact settings } }",
        context_value={"posts": ["Jam", "Tea"], "admin": True},
    )

    assert not result.errors
    assert result.data == {
        "user": {
            "name": "Ada",
            "greeting": "Hi Ada?",
            "posts": [{"title": "Jam"}],
            "contact": "ada@example.com",
            "settings": {"theme": "dark"},
        }
    }


def test_permissions():
    result = schema.execute_sync("{ user { contact } }", context_value={"admin": False})

    assert result.errors
    assert result.errors[0].message == "Admins only"


def test_resolvers_are_still_methods():
    user = User(name="Ada")

    assert user.greeting("?") == "Hi Ada?"
    assert user.model_dump() == {"name": "Ada"}


def test_resolver_fields_are_inherited():
    class GreeterBase(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field
        def greeting(self) -> str:
            return f"Hi {self.name}"

        @strawberry.pydantic.field
        def farewell(self) -> str:
            return f"Bye {self.name}"

    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: strawberry.ID

        @strawberry.pydantic.field
        def global_id(self) -> str:
            return f"{type(self).__name__}:{self.id}"

    @strawberry.pydantic.type
    class Person(Node, GreeterBase):
        @strawberry.pydantic.field
        def greeting(self) -> str:
            return f"Hello {self.name}"

        # not a field anymore
        def farewell(self) -> str:
            return "Bye"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person(id=strawberry.ID("1"), name="Ada")

    schema = strawberry.Schema(query=Query)

    assert "farewell" not in str(schema)

    result = schema.execute_sync("{ person { greeting globalId } }")

    assert not result.errors
    assert result.data == {"person": {"greeting": "Hello Ada", "globalId": "Person:1"}}


def test_strawberry_field_when_pydantic_ignores_it():
    @strawberry.pydantic.type
    class Admin(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(ignored_types=(StrawberryField,))

        name: str

        @strawberry.field
        def shout(self) -> str:
            return self.name.upper()

    @strawberry.type
    class Query:
        @strawberry.field
        def admin(self) -> Admin:
            return Admin(name="root")

    result = strawberry.Schema(query=Query).execute_sync("{ admin { name shout } }")

    assert not result.errors
    assert result.data == {"admin": {"name": "root", "shout": "ROOT"}}


@pytest.mark.raises_strawberry_exception(
    ResolverFieldOnInputError,
    match="Field `upper` on pydantic input `NameInput` can't have a resolver",
)
def test_resolver_fields_on_inputs_raise_an_error():
    @strawberry.pydantic.input
    class NameInput(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field
        def upper(self) -> str:
            return self.name.upper()


def _query(model_type: type, instance: object, query: str) -> Any:
    @strawberry.type
    class Query:
        @strawberry.field
        def item(self) -> model_type:  # type: ignore[valid-type]
            return instance

    return strawberry.Schema(query=Query).execute_sync(query)


def test_decorators_above_the_marker_are_used():
    def uppercase(resolver: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(resolver)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            return resolver(*args, **kwargs).upper()

        return wrapper

    @strawberry.pydantic.type
    class Greeter(pydantic.BaseModel):
        name: str

        @uppercase
        @strawberry.pydantic.field
        def greeting(self, punctuation: str = "!") -> str:
            return f"hi {self.name}{punctuation}"

    result = _query(
        Greeter, Greeter(name="Ada"), '{ item { greeting(punctuation: "?") } }'
    )

    assert not result.errors
    assert result.data == {"item": {"greeting": "HI ADA?"}}


def test_resolvers_with_other_decorators():
    @strawberry.pydantic.type
    class Model(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(frozen=True)

        name: str

        @staticmethod
        @strawberry.pydantic.field
        def static_below() -> int:
            return 1

        @strawberry.pydantic.field
        @staticmethod
        def static_above() -> int:
            return 2

        @classmethod
        @strawberry.pydantic.field
        def class_below(cls) -> str:
            return cls.__name__

        @functools.cache
        @strawberry.pydantic.field
        def cached(self) -> str:
            return self.name.upper()

    result = _query(
        Model,
        Model(name="ada"),
        "{ item { staticBelow staticAbove classBelow cached } }",
    )

    assert not result.errors
    assert result.data == {
        "item": {
            "staticBelow": 1,
            "staticAbove": 2,
            "classBelow": "Model",
            "cached": "ADA",
        }
    }


def test_fields_are_named_after_their_attribute():
    def get_label(self: Any) -> str:
        return f"#{self.id}"

    @strawberry.pydantic.type
    class Ticket(pydantic.BaseModel):
        id: int

        label = strawberry.pydantic.field(get_label)

    result = _query(Ticket, Ticket(id=1), "{ item { label } }")

    assert not result.errors
    assert result.data == {"item": {"label": "#1"}}


@pytest.mark.raises_strawberry_exception(
    ResolverAlreadyUsedError,
    match=(
        "`get_label` is already the resolver of a field, a resolver can only be "
        "used by one `strawberry.pydantic.field`"
    ),
)
def test_a_resolver_can_only_be_used_once():
    def get_label(self: Any) -> str:
        return "label"

    strawberry.pydantic.field(get_label)
    strawberry.pydantic.field(name="title")(get_label)


def test_resolvers_need_a_return_annotation():
    with pytest.raises(MissingReturnAnnotationError):

        @strawberry.pydantic.field
        def label(self):
            return "label"


def test_data_fields_override_inherited_resolver_fields():
    class Base(pydantic.BaseModel):
        @strawberry.pydantic.field
        def name(self) -> str:
            return "from the resolver"

    with pytest.warns(UserWarning, match="shadows an attribute in parent"):

        @strawberry.pydantic.type
        class Child(Base):
            name: str  # type: ignore[assignment]

    result = _query(Child, Child(name="from the data"), "{ item { name } }")

    assert not result.errors
    assert result.data == {"item": {"name": "from the data"}}


@pytest.mark.raises_strawberry_exception(
    ResolverFieldOverridesModelFieldError,
    match="The resolver of `name` on pydantic model `Child` overrides a model field",
)
def test_resolvers_cannot_override_model_fields():
    class Base(pydantic.BaseModel):
        name: str

    @strawberry.pydantic.type
    class Child(Base):
        @strawberry.pydantic.field
        def name(self) -> str:  # type: ignore[override]
            return "Ada"


def test_resolvers_of_generic_models():
    @strawberry.pydantic.type
    class Item(pydantic.BaseModel):
        name: str

    class Page(pydantic.BaseModel, Generic[T]):
        items: list[T]

        @strawberry.pydantic.field
        def first(self) -> T | None:
            return self.items[0] if self.items else None

    @strawberry.pydantic.type
    class ItemPage(Page[Item]):
        pass

    @strawberry.pydantic.type
    class IntPage(Page[int]):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> ItemPage:
            return ItemPage(items=[Item(name="jam")])

        @strawberry.field
        def numbers(self) -> IntPage:
            return IntPage(items=[1, 2])

    schema = strawberry.Schema(query=Query)

    assert "first: Item" in str(schema)
    assert "first: Int" in str(schema)

    result = schema.execute_sync("{ items { first { name } } numbers { first } }")

    assert not result.errors
    assert result.data == {"items": {"first": {"name": "jam"}}, "numbers": {"first": 1}}


def test_graphql_type_forward_references():
    @strawberry.pydantic.type
    class Author(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field(graphql_type=list["Book"])
        def books(self) -> list[Any]:
            return [Book(title="Notes")]

    result = _query(Author, Author(name="Ada"), "{ item { books { title } } }")

    assert not result.errors
    assert result.data == {"item": {"books": [{"title": "Notes"}]}}


def test_inputs_ignore_inherited_resolver_fields():
    class UserBase(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field
        def greeting(self) -> str:
            return f"Hi {self.name}"

    @strawberry.pydantic.type
    class UserType(UserBase):
        pass

    @strawberry.pydantic.input
    class UserInput(UserBase):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, input: UserInput) -> UserType:
            return UserType(name=input.name)

    input_fields = get_object_definition(UserInput, strict=True).fields

    assert [field.python_name for field in input_fields] == ["name"]

    result = strawberry.Schema(query=Query).execute_sync(
        '{ user(input: {name: "Ada"}) { greeting } }'
    )

    assert not result.errors
    assert result.data == {"user": {"greeting": "Hi Ada"}}
