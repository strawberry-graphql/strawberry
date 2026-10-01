import textwrap
from typing import Optional

import pydantic
import pytest

import strawberry
from strawberry.exceptions import UnresolvedFieldTypeError

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
