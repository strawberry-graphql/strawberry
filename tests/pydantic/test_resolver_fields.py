import functools
import inspect
from collections.abc import AsyncIterator, Callable
from typing import Annotated, Any, Generic, TypeVar

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.exceptions import (
    MissingReturnAnnotationError,
    ResolverFieldOnInputError,
)
from strawberry.pydantic.exceptions import (
    MisplacedFieldError,
    StrawberryBaseBeforeModelError,
    UnregisteredPydanticTypeError,
    UnsupportedFieldOverrideError,
    UnsupportedInheritedFieldError,
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

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person(id=strawberry.ID("1"), name="Ada")

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ person { greeting farewell globalId } }")

    assert not result.errors
    assert result.data == {
        "person": {
            "greeting": "Hello Ada",
            "farewell": "Bye Ada",
            "globalId": "Person:1",
        }
    }


@pytest.mark.raises_strawberry_exception(
    UnsupportedFieldOverrideError,
    match=(
        "`greeting` on `Admin` overrides an inherited field with a resolver, but "
        "isn't a field itself"
    ),
)
def test_methods_cannot_override_inherited_resolver_fields():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field
        def greeting(self) -> str:
            return f"Hi {self.name}"

    @strawberry.pydantic.type
    class Admin(User):
        def greeting(self) -> str:
            return f"Welcome back, {self.name}"


@pytest.mark.raises_strawberry_exception(
    UnsupportedFieldOverrideError,
    match=(
        "`greeting` on `Base` overrides an inherited field with a resolver, but "
        "isn't a field itself"
    ),
)
def test_methods_of_undecorated_bases_cannot_override_resolver_fields():
    class Greeter(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field
        def greeting(self) -> str:
            return f"Hi {self.name}"

    class Base(Greeter):
        @property
        def greeting(self) -> str:  # type: ignore[override]
            return "Hi"

    @strawberry.pydantic.type
    class User(Base):
        pass


def test_computed_fields_override_inherited_resolver_fields():
    class Base(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field
        def display(self) -> int:
            return len(self.name)

    @strawberry.pydantic.type
    class Child(Base):
        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def display(self) -> str:  # type: ignore[override]
            return self.name.upper()

    result = _query(Child, Child(name="Ada"), "{ item { display } }")

    assert not result.errors
    assert result.data == {"item": {"display": "ADA"}}


@pytest.mark.raises_strawberry_exception(
    UnsupportedFieldOverrideError,
    match=(
        "`display` on `Child` overrides an inherited field with a resolver, but "
        "isn't a field itself"
    ),
)
def test_excluded_computed_fields_cannot_override_inherited_resolver_fields():
    class Base(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field
        def display(self) -> int:
            return len(self.name)

    @strawberry.pydantic.type(include_computed=False)
    class Child(Base):
        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def display(self) -> str:  # type: ignore[override]
            return self.name.upper()


@pytest.mark.raises_strawberry_exception(
    UnsupportedFieldOverrideError,
    match=(
        "`display` on `Child` overrides an inherited field with a resolver, but "
        "isn't a field itself"
    ),
)
def test_methods_cannot_override_resolver_fields_named_like_computed_fields():
    class Base(pydantic.BaseModel):
        name: str

        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def display(self) -> str:
            return self.name

    class Parent(Base):
        @strawberry.pydantic.field
        def display(self) -> int:  # type: ignore[override]
            return len(self.name)

    @strawberry.pydantic.type
    class Child(Parent):
        def display(self) -> int:  # type: ignore[override]
            return 0


@pytest.mark.raises_strawberry_exception(
    UnsupportedFieldOverrideError,
    match=(
        "`double` on `Child` overrides an inherited computed field, but isn't a "
        "field itself"
    ),
)
def test_methods_cannot_override_inherited_computed_fields():
    class Base(pydantic.BaseModel):
        value: int

        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def double(self) -> int:
            return self.value * 2

    @strawberry.pydantic.type
    class Child(Base):
        def double(self) -> int:  # type: ignore[override]
            return 0


def test_properties_can_override_inherited_computed_fields():
    class Base(pydantic.BaseModel):
        value: int

        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def double(self) -> int:
            return self.value * 2

    # pydantic reads the value of the computed field from the new property
    @strawberry.pydantic.type
    class Child(Base):
        @property
        def double(self) -> int:  # type: ignore[override]
            return self.value * 3

    result = _query(Child, Child(value=2), "{ item { double } }")

    assert not result.errors
    assert result.data == {"item": {"double": 6}}


@pytest.mark.raises_strawberry_exception(
    UnsupportedInheritedFieldError,
    match=(
        "Pydantic type `Item` can't inherit field `label` from `Labelled`, as it "
        "has a resolver"
    ),
)
def test_fields_with_a_resolver_inherited_from_strawberry_types_raise_an_error():
    def get_label() -> str:
        return "label"

    @strawberry.interface
    class Labelled:
        label: str = strawberry.field(resolver=get_label)

    @strawberry.pydantic.type
    class Item(pydantic.BaseModel, Labelled):
        id: int


async def test_resolver_fields_inherited_from_strawberry_interfaces():
    @strawberry.interface
    class Node:
        id: strawberry.ID

        @strawberry.field
        def display_name(self) -> str:
            return f"Node {self.id}"

        @strawberry.field
        async def label(self, prefix: str = "#") -> str:
            return f"{prefix}{self.id}"

    @strawberry.pydantic.type
    class Product(pydantic.BaseModel, Node):
        title: str

    @strawberry.type
    class Article(Node):
        body: str

    @strawberry.type
    class Query:
        @strawberry.field
        def nodes(self) -> list[Node]:
            return [
                Product(id=strawberry.ID("1"), title="Jam"),
                Article(id=strawberry.ID("2"), body="Hi"),
            ]

    schema = strawberry.Schema(query=Query, types=[Product, Article])

    assert str(schema) == snapshot("""\
type Article implements Node {
  id: ID!
  displayName: String!
  label(prefix: String! = "#"): String!
  body: String!
}

interface Node {
  id: ID!
  displayName: String!
  label(prefix: String! = "#"): String!
}

type Product implements Node {
  id: ID!
  title: String!
  displayName: String!
  label(prefix: String! = "#"): String!
}

type Query {
  nodes: [Node!]!
}\
""")

    result = await schema.execute(
        '{ nodes { id displayName label(prefix: "n") '
        "... on Product { title } ... on Article { body } } }"
    )

    assert not result.errors
    assert result.data == {
        "nodes": [
            {"id": "1", "displayName": "Node 1", "label": "n1", "title": "Jam"},
            {"id": "2", "displayName": "Node 2", "label": "n2", "body": "Hi"},
        ]
    }
    # the resolvers aren't fields of the model
    assert list(Product.model_fields) == ["id", "title"]


def test_resolver_fields_inherited_from_strawberry_types_keep_their_options():
    @strawberry.type
    class Account:
        @strawberry.field(name="secret", permission_classes=[IsAdmin])
        def get_secret(self) -> str:
            return "hunter2"

    @strawberry.pydantic.type
    class User(pydantic.BaseModel, Account):
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="Ada")

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ user { secret } }", context_value={"admin": False})

    assert result.errors
    assert result.errors[0].message == "Admins only"

    result = schema.execute_sync("{ user { secret } }", context_value={"admin": True})

    assert not result.errors
    assert result.data == {"user": {"secret": "hunter2"}}


def test_static_and_class_methods_inherited_from_strawberry_types_are_bound():
    @strawberry.interface
    class Versioned:
        @strawberry.field
        @staticmethod
        def version() -> int:
            return 2

        @strawberry.field
        @classmethod
        def kind(cls) -> str:
            return cls.__name__

    @strawberry.pydantic.type
    class Item(pydantic.BaseModel, Versioned):
        id: int

    result = _query(Item, Item(id=1), "{ item { version kind } }")

    assert not result.errors
    # like with `@strawberry.type`, the class method gets the type using it
    assert result.data == {"item": {"version": 2, "kind": "Item"}}


def test_resolver_fields_inherited_from_strawberry_types_can_be_overridden():
    @strawberry.interface
    class Named:
        @strawberry.field
        def name(self) -> str:
            return "named"

    @strawberry.pydantic.type
    class Product(pydantic.BaseModel, Named):
        @strawberry.pydantic.field
        def name(self) -> str:
            return "product"

    @strawberry.pydantic.type
    class Person(pydantic.BaseModel, Named):
        name: str

    result = _query(Product, Product(), "{ item { name } }")

    assert not result.errors
    assert result.data == {"item": {"name": "product"}}

    result = _query(Person, Person(name="Ada"), "{ item { name } }")

    assert not result.errors
    assert result.data == {"item": {"name": "Ada"}}


@pytest.mark.raises_strawberry_exception(
    UnsupportedFieldOverrideError,
    match=(
        "`name` on `Product` overrides an inherited field with a resolver, but "
        "isn't a field itself"
    ),
)
def test_methods_overriding_resolver_fields_of_strawberry_types_raise_an_error():
    @strawberry.interface
    class Named:
        @strawberry.field
        def name(self) -> str:
            return "named"

    @strawberry.pydantic.type
    class Product(pydantic.BaseModel, Named):
        def name(self) -> str:
            return "product"


def test_pydantic_interfaces_can_extend_strawberry_interfaces():
    @strawberry.interface
    class Node:
        id: strawberry.ID

        @strawberry.field
        def display_name(self) -> str:
            return f"Node {self.id}"

    @strawberry.pydantic.interface
    class Named(pydantic.BaseModel, Node):
        name: str

    @strawberry.pydantic.type
    class Person(Named):
        email: str

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self) -> Node:
            return Person(id=strawberry.ID("1"), name="Ada", email="ada@example.com")

    schema = strawberry.Schema(query=Query, types=[Person])

    assert "type Person implements Named & Node {" in str(schema)

    result = schema.execute_sync(
        "{ node { id displayName ... on Named { name } ... on Person { email } } }"
    )

    assert not result.errors
    assert result.data == {
        "node": {
            "id": "1",
            "displayName": "Node 1",
            "name": "Ada",
            "email": "ada@example.com",
        }
    }


@pytest.mark.raises_strawberry_exception(
    StrawberryBaseBeforeModelError,
    match=(
        "Pydantic type `Product` extends the Strawberry interface `Node` before a "
        "Pydantic model$"
    ),
)
def test_strawberry_bases_before_the_model_raise_an_error():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    # `Node`'s dataclass `__init__` would replace Pydantic's
    @strawberry.pydantic.type
    class Product(Node, pydantic.BaseModel):
        title: str


def test_strawberry_bases_before_the_model_suggest_listing_the_models_first():
    @strawberry.input
    class Pagination:
        first: int = 10

    class SearchBase(pydantic.BaseModel):
        query: str

    with pytest.raises(StrawberryBaseBeforeModelError) as exc_info:

        @strawberry.pydantic.input
        class SearchInput(Pagination, SearchBase):
            pass

    assert str(exc_info.value) == (
        "Pydantic input `SearchInput` extends the Strawberry input `Pagination` "
        "before a Pydantic model"
    )
    assert exc_info.value.suggestion == (
        "The `__init__` of `Pagination` would replace Pydantic's, so the model "
        "couldn't be created. List the Pydantic models first: "
        "`class SearchInput(SearchBase, Pagination)`."
    )


def test_subclasses_can_define_fields_overridden_by_their_bases():
    class Greeter(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field
        def greeting(self) -> str:
            return f"Hi {self.name}"

    class Base(Greeter):
        def greeting(self) -> str:
            return "Hi"

    @strawberry.pydantic.type
    class User(Base):
        @strawberry.pydantic.field
        def greeting(self) -> str:
            return f"Hello {self.name}"

    with pytest.warns(UserWarning, match="shadows an attribute in parent"):

        @strawberry.pydantic.type
        class Admin(Base):
            greeting: str  # type: ignore[assignment]

    result = _query(User, User(name="Ada"), "{ item { greeting } }")

    assert not result.errors
    assert result.data == {"item": {"greeting": "Hello Ada"}}

    result = _query(
        Admin, Admin(name="Ada", greeting="Welcome"), "{ item { greeting } }"
    )

    assert not result.errors
    assert result.data == {"item": {"greeting": "Welcome"}}


@pytest.mark.raises_strawberry_exception(
    MisplacedFieldError,
    match=(
        "Field `shout` on pydantic model `Admin` uses `strawberry.field`, which "
        "pydantic types only read from Strawberry types and interfaces$"
    ),
)
def test_strawberry_fields_in_models_that_ignore_them_raise_an_error():
    # without the error, pydantic would ignore the field, and so would the type
    @strawberry.pydantic.type
    class Admin(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(ignored_types=(StrawberryField,))

        name: str

        @strawberry.field
        def shout(self) -> str:
            return self.name.upper()


def test_strawberry_fields_inherited_from_models_that_ignore_them_raise_an_error():
    class Base(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(ignored_types=(StrawberryField,))

        name: str

        @strawberry.field
        def shout(self) -> str:
            return self.name.upper()

    with pytest.raises(MisplacedFieldError) as exc_info:

        @strawberry.pydantic.type
        class Admin(Base):
            pass

    assert str(exc_info.value) == (
        "Field `shout` on pydantic model `Base` uses `strawberry.field`, which "
        "pydantic types only read from Strawberry types and interfaces"
    )
    assert exc_info.value.suggestion == (
        "Use `@strawberry.pydantic.field` to add a field with a resolver to a "
        "pydantic model."
    )


def test_strawberry_fields_of_undecorated_classes_raise_an_error():
    # `@strawberry.type` ignores them too, but silently
    class Shouting:
        @strawberry.field
        def shout(self) -> str:
            return "HI"

    with pytest.raises(MisplacedFieldError) as exc_info:

        @strawberry.pydantic.type
        class Admin(pydantic.BaseModel, Shouting):
            name: str

    assert str(exc_info.value) == (
        "Field `shout` on class `Shouting` uses `strawberry.field`, which "
        "pydantic types only read from Strawberry types and interfaces"
    )
    assert exc_info.value.suggestion == (
        "Use `@strawberry.pydantic.field`, or decorate `Shouting` with "
        "`@strawberry.type` or `@strawberry.interface`."
    )


@pytest.mark.raises_strawberry_exception(
    ResolverFieldOnInputError,
    match="Field `shout` on input type `NameInput` can't have a resolver$",
)
def test_strawberry_fields_on_inputs_that_ignore_them_raise_an_error():
    @strawberry.pydantic.input
    class NameInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(ignored_types=(StrawberryField,))

        name: str

        @strawberry.field
        def shout(self) -> str:
            return self.name.upper()


@pytest.mark.raises_strawberry_exception(
    ResolverFieldOnInputError,
    match="Field `upper` on input type `NameInput` can't have a resolver$",
)
def test_resolver_fields_on_inputs_raise_an_error():
    @strawberry.pydantic.input
    class NameInput(pydantic.BaseModel):
        name: str

        @strawberry.pydantic.field
        def upper(self) -> str:
            return self.name.upper()


# `strawberry.pydantic.field` itself, and what it returns when given options
PYDANTIC_FIELD_DECORATORS = pytest.mark.parametrize(
    "decorator",
    [strawberry.pydantic.field, strawberry.pydantic.field(name="yearsOld")],
    ids=["bare", "with-options"],
)


@PYDANTIC_FIELD_DECORATORS
@pytest.mark.raises_strawberry_exception(
    MisplacedFieldError,
    match=(
        "Field `age` on pydantic model `User` uses `strawberry.pydantic.field`, "
        "which is only for fields with a resolver$"
    ),
)
def test_pydantic_field_in_the_annotation_of_a_model_field_raises_an_error(
    decorator: Any,
):
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: Annotated[int, decorator]


@PYDANTIC_FIELD_DECORATORS
@pytest.mark.raises_strawberry_exception(
    MisplacedFieldError,
    match=(
        "Field `age` on pydantic model `UserInput` uses "
        "`strawberry.pydantic.field`, which is only for fields with a resolver$"
    ),
)
def test_pydantic_field_as_the_default_of_a_model_field_raises_an_error(
    decorator: Any,
):
    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        age: int = decorator


@PYDANTIC_FIELD_DECORATORS
@pytest.mark.raises_strawberry_exception(
    MisplacedFieldError,
    match=(
        "Field `age` on pydantic model `User` uses `strawberry.pydantic.field`, "
        "which is only for fields with a resolver$"
    ),
)
def test_pydantic_field_nested_in_the_annotation_of_a_model_field_raises_an_error(
    decorator: Any,
):
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: Annotated[int, decorator] | None = None


@pytest.mark.raises_strawberry_exception(
    MisplacedFieldError,
    match=(
        "Field `age` on pydantic model `User` uses `strawberry.pydantic.field`, "
        "which is only for fields with a resolver$"
    ),
)
def test_pydantic_field_in_the_annotation_of_a_computed_field_raises_an_error():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def age(self) -> Annotated[int, strawberry.pydantic.field(name="yearsOld")]:
            return 1


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


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("binding", [None, staticmethod, classmethod])
async def test_resolvers_can_be_reused(asynchronous, binding):
    def get_label(self: Any, suffix: str = "!") -> str:
        return f"{self.id}{suffix}"

    if binding is staticmethod:

        def get_label(suffix: str = "!") -> str:
            return f"static{suffix}"

    elif binding is classmethod:

        def get_label(cls: type, suffix: str = "!") -> str:
            return f"{cls.__name__}{suffix}"

    resolver = get_label
    if asynchronous:

        @functools.wraps(get_label)
        async def resolver(*args: Any, **kwargs: Any) -> str:
            return get_label(*args, **kwargs)

    if binding:
        resolver = binding(resolver)

    @strawberry.pydantic.type
    class Ticket(pydantic.BaseModel):
        id: int

        label = strawberry.pydantic.field(description="Public label")(resolver)
        protected = strawberry.pydantic.field(
            name="title", description="Private title", permission_classes=[IsAdmin]
        )(resolver)

    @strawberry.pydantic.type
    class Issue(pydantic.BaseModel):
        id: int

        label = strawberry.pydantic.field(resolver)

    @strawberry.type
    class Query:
        @strawberry.field
        def ticket(self) -> Ticket:
            return Ticket(id=7)

        @strawberry.field
        def issue(self) -> Issue:
            return Issue(id=9)

    schema = strawberry.Schema(query=Query)
    prefix = "static" if binding is staticmethod else "Ticket" if binding else "7"
    result = await schema.execute(
        '{ ticket { label title(suffix: "?") } }', context_value={"admin": True}
    )
    assert not result.errors
    assert result.data == {"ticket": {"label": f"{prefix}!", "title": f"{prefix}?"}}
    result = await schema.execute(
        "{ ticket { label } }", context_value={"admin": False}
    )
    assert not result.errors
    assert result.data == {"ticket": {"label": f"{prefix}!"}}
    result = await schema.execute(
        "{ ticket { title } }", context_value={"admin": False}
    )
    assert result.errors
    assert result.errors[0].message == "Admins only"
    assert '"""Public label"""' in str(schema)
    assert '"""Private title"""' in str(schema)

    result = await schema.execute("{ issue { label } }", context_value={"admin": False})
    issue_prefix = "static" if binding is staticmethod else "Issue" if binding else "9"
    assert not result.errors
    assert result.data == {"issue": {"label": f"{issue_prefix}!"}}

    value = Ticket(id=7).label(".")
    if asynchronous:
        value = await value
    assert value == f"{prefix}."


@pytest.mark.parametrize("kind", ["bound", "callable", "partial"])
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_callable_resolvers_preserve_binding_and_per_field_options(
    kind, asynchronous
):
    class Formatter:
        def __init__(self, prefix: str):
            self.prefix = prefix

        def __call__(self, suffix: str = "!") -> str:
            return f"{self.prefix}{suffix}"

    class AsyncFormatter(Formatter):
        async def __call__(self, suffix: str = "!") -> str:
            return super().__call__(suffix)

    resolver = AsyncFormatter("label") if asynchronous else Formatter("label")
    if kind == "bound":
        resolver = resolver.__call__
    elif kind == "partial":
        resolver = functools.partial(resolver)

    @strawberry.pydantic.type
    class Ticket(pydantic.BaseModel):
        label = strawberry.pydantic.field(resolver=resolver, description="Public")
        protected = strawberry.pydantic.field(
            resolver,
            name="title",
            description="Private",
            permission_classes=[IsAdmin],
        )

    @strawberry.pydantic.type
    class Issue(pydantic.BaseModel):
        label = strawberry.pydantic.field(resolver)

    @strawberry.type
    class Query:
        @strawberry.field
        def ticket(self) -> Ticket:
            return Ticket()

        @strawberry.field
        def issue(self) -> Issue:
            return Issue()

    schema = strawberry.Schema(query=Query)
    result = await schema.execute(
        '{ ticket { label title(suffix: "?") } issue { label } }',
        context_value={"admin": True},
    )
    assert not result.errors
    assert result.data == {
        "ticket": {"label": "label!", "title": "label?"},
        "issue": {"label": "label!"},
    }
    if not asynchronous:
        synchronous = schema.execute_sync("{ ticket { label } }")
        assert not synchronous.errors
        assert synchronous.data == {"ticket": {"label": "label!"}}
    result = await schema.execute(
        "{ ticket { label } issue { label } }", context_value={"admin": False}
    )
    assert not result.errors
    result = await schema.execute(
        "{ ticket { title } }", context_value={"admin": False}
    )
    assert result.errors
    assert result.errors[0].message == "Admins only"
    assert '"""Public"""' in str(schema)
    assert '"""Private"""' in str(schema)
    assert not hasattr(resolver, "__strawberry_field__")
    assert Ticket().model_dump() == {}

    for owner in (Ticket, Ticket(), Issue, Issue()):
        assert inspect.iscoroutinefunction(owner.label) is asynchronous
        value = owner.label(".")
        if asynchronous:
            value = await value
        assert value == "label."


async def test_async_generator_callable_resolver():
    class Events:
        async def __call__(self, count: int = 2) -> AsyncIterator[int]:
            for value in range(count):
                yield value

    @strawberry.pydantic.type
    class Feed(pydantic.BaseModel):
        events = strawberry.pydantic.field(resolver=Events())

    definition = get_object_definition(Feed, strict=True)
    assert definition.fields[0].is_async
    assert inspect.isasyncgenfunction(Feed().events)
    assert [value async for value in Feed().events(3)] == [0, 1, 2]


@pytest.mark.parametrize("kind", ["partial", "bound", "callable"])
def test_callable_resolvers_with_explicit_root(kind):
    def get_label(prefix: str, root: Any) -> str:
        return f"{prefix}{root.id}"

    class Formatter:
        def __call__(self, root: Any) -> str:
            return get_label("#", root)

    resolver = functools.partial(get_label, "#")
    if kind == "bound":
        resolver = Formatter().__call__
    elif kind == "callable":
        resolver = Formatter()

    @strawberry.pydantic.type
    class Ticket(pydantic.BaseModel):
        id: int

        label = strawberry.pydantic.field(graphql_type=str)(resolver)

    result = _query(Ticket, Ticket(id=1), "{ item { label } }")

    assert not result.errors
    assert result.data == {"item": {"label": "#1"}}

    # These aren't model methods: callers still supply the explicit root.
    assert Ticket(id=2).label(Ticket(id=3)) == "#3"


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
    UnsupportedFieldOverrideError,
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


def test_resolvers_of_generic_models_use_the_graphql_type_of_pydantic_types():
    class Page(pydantic.BaseModel, Generic[T]):
        items: list[T]

        @strawberry.pydantic.field
        def first(self) -> T:
            return self.items[0]

    @strawberry.pydantic.type
    class UrlPage(Page[pydantic.HttpUrl]):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def page(self) -> UrlPage:
            return UrlPage.model_validate({"items": ["https://example.com"]})

    schema = strawberry.Schema(query=Query)

    assert "first: String!" in str(schema)

    result = schema.execute_sync("{ page { first } }")

    assert not result.errors
    assert result.data == {"page": {"first": "https://example.com/"}}


@pytest.mark.raises_strawberry_exception(
    UnregisteredPydanticTypeError,
    match=(
        r"`AddressLookup\.value` uses `Address`, which isn't a Strawberry type: "
        r"decorate it with `@strawberry\.pydantic\.type`"
    ),
)
def test_resolvers_of_generic_models_using_undecorated_models_raise_an_error():
    class Address(pydantic.BaseModel):
        city: str

    class Lookup(pydantic.BaseModel, Generic[T]):
        key: str

        @strawberry.pydantic.field
        def value(self) -> T:
            raise NotImplementedError

    @strawberry.pydantic.type
    class AddressLookup(Lookup[Address]):
        pass


def test_resolvers_of_generic_models_with_type_parameters_of_the_same_name():
    class Page(pydantic.BaseModel, Generic[T]):
        @strawberry.pydantic.field
        def first(self) -> T:
            return 1  # type: ignore[return-value]

    class Sorted(pydantic.BaseModel, Generic[T]):
        @strawberry.pydantic.field
        def sorted_by(self) -> T:
            return "name"  # type: ignore[return-value]

    @strawberry.pydantic.type
    class SortedPage(Page[int], Sorted[str]):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def page(self) -> SortedPage:
            return SortedPage()

    schema = strawberry.Schema(query=Query)

    assert "first: Int!" in str(schema)
    assert "sortedBy: String!" in str(schema)

    result = schema.execute_sync("{ page { first sortedBy } }")

    assert not result.errors
    assert result.data == {"page": {"first": 1, "sortedBy": "name"}}


def test_resolvers_of_generic_models_given_a_type_parameter_of_their_subclass():
    class Page(pydantic.BaseModel, Generic[T]):
        items: list[T]

        @strawberry.pydantic.field
        def first(self) -> T | None:
            return self.items[0] if self.items else None

    class ListPage(Page[list[T]], Generic[T]):
        pass

    @strawberry.pydantic.type
    class IntListPage(ListPage[int]):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def page(self) -> IntListPage:
            return IntListPage(items=[[1, 2]])

    schema = strawberry.Schema(query=Query)

    assert "first: [Int!]\n" in str(schema)

    result = schema.execute_sync("{ page { first items } }")

    assert not result.errors
    assert result.data == {"page": {"first": [1, 2], "items": [[1, 2]]}}


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
