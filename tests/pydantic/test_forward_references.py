import re
import textwrap
from typing import Annotated, Any, Optional

import pydantic
import pytest

import strawberry
from strawberry.exceptions import UnresolvedFieldTypeError
from strawberry.pydantic.exceptions import UnresolvedAnnotatedFieldError

# Self-referencing models are defined at module level, like real apps do: before
# Python 3.12 pydantic can leave `list["Category"]` unresolved, and Strawberry then
# resolves it from the module, as it does for `@strawberry.type`.


@strawberry.pydantic.type
class Category(pydantic.BaseModel):
    name: str
    parent: Optional["Category"] = None
    children: list["Category"] = []


@strawberry.pydantic.input
class Filter(pydantic.BaseModel):
    name: str | None = None
    any_of: list["Filter"] = []


class IsAdmin(strawberry.BasePermission):
    message = "Admins only"

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return False


# Models that reference each other, with `Annotated` options on both sides: with
# only the types quoted, pydantic reads the options right away
@strawberry.pydantic.type
class Writer(pydantic.BaseModel):
    name: str
    articles: Annotated[
        list["Article"], strawberry.field(permission_classes=[IsAdmin])
    ] = []
    draft: Annotated[Optional["Article"], pydantic.Field(description="A draft")] = None
    archived: Annotated[list["Article"], pydantic.Field(exclude=True)] = []


@strawberry.pydantic.type
class Article(pydantic.BaseModel):
    title: str
    writer: Annotated[Writer, strawberry.field(description="The writer")]


def test_self_referencing_model():
    @strawberry.type
    class Query:
        @strawberry.field
        def category(self) -> Category:
            return Category(name="Fruit", children=[Category(name="Strawberry")])

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Category {
      name: String!
      parent: Category
      children: [Category!]!
    }

    type Query {
      category: Category!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync("{ category { name children { name } } }")

    assert not result.errors
    assert result.data == {
        "category": {"name": "Fruit", "children": [{"name": "Strawberry"}]}
    }


def test_self_referencing_input():
    @strawberry.type
    class Query:
        @strawberry.field
        def names(self, where: Filter) -> list[str]:
            return [item.name for item in where.any_of if item.name]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ names(where: { anyOf: [{ name: "Ada" }] }) }')

    assert not result.errors
    assert result.data == {"names": ["Ada"]}


@pytest.mark.raises_strawberry_exception(
    UnresolvedAnnotatedFieldError,
    match=re.escape(
        "The `Annotated` options of field `account` on pydantic model `Owner` "
        "can't be read because its annotation uses names that aren't defined yet"
    )
    + "$",
)
def test_quoted_annotated_with_a_model_defined_later_raises_an_error():
    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        account: "Annotated[Account, strawberry.field(description='The account')]"

    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        iban: str


def test_models_referencing_each_other_with_annotated_options():
    @strawberry.type
    class Query:
        @strawberry.field
        def article(self) -> Article:
            return Article(title="Notes", writer=Writer(name="Ada"))

        @strawberry.field
        def writer(self) -> Writer:
            article = Article(title="Notes", writer=Writer(name="Ada"))

            return Writer(
                name="Ada", articles=[article], draft=article, archived=[article]
            )

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Article {
      title: String!

      \"\"\"The writer\"\"\"
      writer: Writer!
    }

    type Query {
      article: Article!
      writer: Writer!
    }

    type Writer {
      name: String!
      articles: [Article!]!

      \"\"\"A draft\"\"\"
      draft: Article
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync("{ article { writer { name } } }")

    assert not result.errors
    assert result.data == {"article": {"writer": {"name": "Ada"}}}

    result = schema.execute_sync("{ writer { draft { title } } }")

    assert not result.errors
    assert result.data == {"writer": {"draft": {"title": "Notes"}}}

    result = schema.execute_sync("{ writer { articles { title } } }")

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == "Admins only"


def test_lazy_type_with_strawberry_field():
    from tests.pydantic.lazy.account import Account
    from tests.pydantic.lazy.owner import Owner

    # like any pydantic model with a type defined elsewhere
    Owner.model_rebuild(_types_namespace={"Account": Account})

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> Owner:
            return Owner(name="Ada", account=Account(iban="secret"))

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Account {
      iban: String!
    }

    type Owner {
      name: String!
      account: Account!
    }

    type Query {
      owner: Owner!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync("{ owner { name account { iban } } }")

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == "Admins only"


def test_lazy_type_with_future_annotations():
    from tests.pydantic.lazy.account import Account
    from tests.pydantic.lazy.owner_future_annotations import Owner

    Owner.model_rebuild(_types_namespace={"Account": Account})

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> Owner:
            account = Account(iban="NL01")

            return Owner(name="Ada", account=account, accounts=[account])

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Account {
      iban: String!
    }

    type Owner {
      name: String!
      account: Account!
      accounts: [Account!]!
    }

    type Query {
      owner: Owner!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync("{ owner { account { iban } accounts { iban } } }")

    assert not result.errors
    assert result.data == {
        "owner": {"account": {"iban": "NL01"}, "accounts": [{"iban": "NL01"}]}
    }


@pytest.mark.xfail(
    raises=UnresolvedFieldTypeError,
    strict=True,
    reason=(
        "Models that import each other aren't supported yet: the Strawberry field "
        "keeps the forward reference pydantic had when the model was decorated, "
        "and doesn't see the type resolved by `model_rebuild()`"
    ),
)
def test_models_importing_each_other():
    from tests.pydantic.circular.author import Author
    from tests.pydantic.circular.book import Book

    @strawberry.type
    class Query:
        @strawberry.field
        def author(self) -> Author:
            return Author(name="Ada", books=[Book(title="Notes")])

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Author {
      name: String!
      books: [Book!]!
    }

    type Book {
      title: String!
      author: Author
    }

    type Query {
      author: Author!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync("{ author { name books { title } } }")

    assert not result.errors
    assert result.data == {"author": {"name": "Ada", "books": [{"title": "Notes"}]}}
