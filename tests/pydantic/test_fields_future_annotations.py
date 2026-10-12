from __future__ import annotations

import re
import textwrap
import typing
from typing import TYPE_CHECKING, Annotated, Any, Optional, TypeVar

import pydantic
import pytest

import strawberry
from strawberry import Private
from strawberry.pydantic.exceptions import UnresolvedAnnotatedFieldError
from strawberry.types.base import get_object_definition

# Types are defined at module level: with postponed annotations, Strawberry
# resolves the resolvers' string annotations from the module namespace.


class IsAdmin(strawberry.BasePermission):
    message = "Admins only"

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return False


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: Annotated[
        str,
        strawberry.field(
            name="fullName",
            description="The full name",
            deprecation_reason="Use displayName",
        ),
    ]
    email: Annotated[str, strawberry.field(permission_classes=[IsAdmin])]
    password: strawberry.Private[str]


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Ada", email="ada@example.com", password="secret")


schema = strawberry.Schema(query=Query)


# `Book` is defined below: pydantic resolves these annotations once it's defined,
# and Strawberry when the schema is built
@strawberry.pydantic.type
class Library(pydantic.BaseModel):
    featured: Book
    books: list[Book]
    sequel: Book | None = None
    archive: strawberry.Private[list[Book]] = []
    drafts: Private[list[Book]] = []


@strawberry.pydantic.type
class Book(pydantic.BaseModel):
    title: str


# Strawberry reads `strawberry.union()` when it resolves the annotation
@strawberry.pydantic.type
class Feed(pydantic.BaseModel):
    item: Annotated[Post | Video, strawberry.union("FeedItem")]


@strawberry.pydantic.type
class Post(pydantic.BaseModel):
    title: str


@strawberry.pydantic.type
class Video(pydantic.BaseModel):
    url: str


# The `Annotated` options can only be read once `Wallet` is defined, so
# `Customer` is decorated after it
class Customer(pydantic.BaseModel):
    wallet: Annotated[Wallet, strawberry.field(permission_classes=[IsAdmin])]
    savings: Annotated[Wallet | None, pydantic.Field(description="The savings")] = None
    hidden: Annotated[Wallet | None, pydantic.Field(exclude=True)] = None


@strawberry.pydantic.type
class Wallet(pydantic.BaseModel):
    balance: int


Customer.model_rebuild()
strawberry.pydantic.type(Customer)


T = TypeVar("T")

AdminOnly = Annotated[T, strawberry.field(permission_classes=[IsAdmin])]
# `Account` is defined by the test that uses the alias
HiddenAccount = Annotated[Optional["Account"], pydantic.Field(exclude=True)]  # noqa: F821


def _unresolved_annotated(field_name: str, model_name: str) -> str:
    """Match the message of `UnresolvedAnnotatedFieldError`."""
    message = (
        f"The `Annotated` options of field `{field_name}` on pydantic model "
        f"`{model_name}` can't be read because its annotation uses names that "
        "aren't defined yet"
    )

    return re.escape(message) + "$"


def test_private_fields_are_excluded():
    assert "password" not in str(schema)

    result = schema.execute_sync("{ user { password } }")

    assert result.errors
    assert result.errors[0].message == "Cannot query field 'password' on type 'User'."


def test_annotated_permissions_are_enforced():
    result = schema.execute_sync("{ user { fullName email } }")

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == "Admins only"


def test_annotated_field_options_are_used():
    name_field = next(
        field
        for field in get_object_definition(User, strict=True).fields
        if field.python_name == "name"
    )

    assert name_field.graphql_name == "fullName"
    assert name_field.description == "The full name"
    assert name_field.deprecation_reason == "Use displayName"


def test_forward_references_without_annotated():
    @strawberry.type
    class Query:
        @strawberry.field
        def library(self) -> Library:
            book = Book(title="Dune")

            return Library(featured=book, books=[book], archive=[book], drafts=[book])

    library_schema = strawberry.Schema(query=Query)

    # `archive` and `drafts` are private
    expected_schema = """
    type Book {
      title: String!
    }

    type Library {
      featured: Book!
      books: [Book!]!
      sequel: Book
    }

    type Query {
      library: Library!
    }
    """

    assert str(library_schema) == textwrap.dedent(expected_schema).strip()

    result = library_schema.execute_sync(
        "{ library { featured { title } books { title } sequel { title } } }"
    )

    assert not result.errors
    assert result.data == {
        "library": {
            "featured": {"title": "Dune"},
            "books": [{"title": "Dune"}],
            "sequel": None,
        }
    }


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("account", "Owner")
)
def test_strawberry_field_with_a_model_defined_later_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        account: Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("account", "Owner")
)
def test_excluded_field_with_a_model_defined_later_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        account: Annotated[Account | None, pydantic.Field(exclude=True)] = None

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("account", "Owner")
)
def test_field_description_with_a_model_defined_later_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        account: Annotated[Account, pydantic.Field(description="The account")]

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("account", "Owner")
)
def test_nested_annotated_with_a_model_defined_later_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        account: Optional[
            Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]
        ] = None

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("account", "Owner")
)
def test_typing_annotated_with_a_model_defined_later_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        account: typing.Annotated[Account | None, pydantic.Field(exclude=True)] = None

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("account", "Owner")
)
def test_computed_field_with_a_model_defined_later_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def account(
            self,
        ) -> Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]:
            return Account(iban="secret")

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("account", "Owner")
)
def test_annotated_alias_with_a_model_defined_later_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        account: AdminOnly[Account]

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("hidden", "Owner")
)
def test_annotated_alias_of_a_model_defined_later_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        hidden: HiddenAccount = None

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("account", "Owner")
)
def test_computed_field_with_an_annotated_alias_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def account(self) -> AdminOnly[Account]:
            return Account(iban="secret")

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError, match=_unresolved_annotated("account", "Owner")
)
def test_lazy_type_with_strawberry_field_raises_an_error():
    if TYPE_CHECKING:
        from tests.pydantic.lazy.account import Account

    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        account: Annotated[
            Account,
            strawberry.lazy("tests.pydantic.lazy.account"),
            strawberry.field(permission_classes=[IsAdmin]),
        ]


def test_union_with_members_defined_later():
    @strawberry.type
    class Query:
        @strawberry.field
        def feed(self) -> Feed:
            return Feed(item=Video(url="https://example.com"))

    feed_schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Feed {
      item: FeedItem!
    }

    union FeedItem = Post | Video

    type Post {
      title: String!
    }

    type Query {
      feed: Feed!
    }

    type Video {
      url: String!
    }
    """

    assert str(feed_schema) == textwrap.dedent(expected_schema).strip()

    result = feed_schema.execute_sync("{ feed { item { __typename } } }")

    assert not result.errors
    assert result.data == {"feed": {"item": {"__typename": "Video"}}}


def test_inherited_annotated_field_with_a_model_defined_later():
    class Base(pydantic.BaseModel):
        account: Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]

    class Owner(Base):
        name: str

    with pytest.raises(UnresolvedAnnotatedFieldError) as exc_info:
        strawberry.pydantic.type(Owner)

    # the error points to the field, and the suggestion to the decorated model
    assert re.match(_unresolved_annotated("account", "Base"), str(exc_info.value))
    assert (
        "Define the models the annotation references before `Base`, or decorate "
        "`Owner` later: once they're defined, call `Owner.model_rebuild()` and then "
        "decorate it."
    ) in exc_info.value.suggestion

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str

    Owner.model_rebuild()
    strawberry.pydantic.type(Owner)

    [account_field, _] = get_object_definition(Owner, strict=True).fields

    assert account_field.permission_classes == [IsAdmin]


def test_annotated_options_with_models_defined_first_are_used():
    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str

    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        account: Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]
        savings: Annotated[
            Account | None, pydantic.Field(description="The savings")
        ] = None
        hidden: Annotated[Account | None, pydantic.Field(exclude=True)] = None

    # `hidden` is excluded
    [account_field, savings_field] = get_object_definition(Owner, strict=True).fields

    assert account_field.permission_classes == [IsAdmin]
    assert savings_field.python_name == "savings"
    assert savings_field.description == "The savings"


def test_annotated_options_of_models_decorated_later_are_used():
    @strawberry.type
    class Query:
        @strawberry.field
        def customer(self) -> Customer:
            wallet = Wallet(balance=10)

            return Customer(wallet=wallet, savings=wallet, hidden=wallet)

    customer_schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Customer {
      wallet: Wallet!

      \"\"\"The savings\"\"\"
      savings: Wallet
    }

    type Query {
      customer: Customer!
    }

    type Wallet {
      balance: Int!
    }
    """

    assert str(customer_schema) == textwrap.dedent(expected_schema).strip()

    result = customer_schema.execute_sync("{ customer { wallet { balance } } }")

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == "Admins only"
