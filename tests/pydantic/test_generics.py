from typing import Annotated, Generic, TypeVar

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.types.base import (
    StrawberryList,
    StrawberryOptional,
    StrawberryTypeVar,
    get_object_definition,
)

T = TypeVar("T")


def test_basic_pydantic_generic_fields():
    """Test that pydantic generic models preserve field types correctly."""

    @strawberry.pydantic.type
    class GenericModel(pydantic.BaseModel, Generic[T]):
        value: T
        name: str = "default"

    definition = get_object_definition(GenericModel, strict=True)

    # Check fields
    fields = definition.fields
    assert len(fields) == 2

    value_field = next(f for f in fields if f.python_name == "value")
    name_field = next(f for f in fields if f.python_name == "name")

    # The value field should contain a TypeVar (generic parameter)
    assert isinstance(value_field.type, StrawberryTypeVar)
    assert value_field.type.type_var is T

    # The name field should be concrete
    assert name_field.type is str


def test_pydantic_generic_with_concrete_type():
    """Test pydantic with a concrete generic instantiation."""

    class GenericModel(pydantic.BaseModel, Generic[T]):
        data: T

    # Create a concrete version by inheriting from GenericModel[int]
    @strawberry.pydantic.type
    class ConcreteModel(GenericModel[int]):
        pass

    definition = get_object_definition(ConcreteModel, strict=True)

    # Verify the field type is concrete
    [data_field] = definition.fields
    assert data_field.python_name == "data"
    assert data_field.type is int


def test_pydantic_generic_schema():
    """Test the GraphQL schema generated from pydantic generic types."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel, Generic[T]):
        id: int
        data: T
        name: str = "default"

    # Create concrete versions
    @strawberry.pydantic.type
    class UserString(User[str]):
        pass

    @strawberry.pydantic.type
    class UserInt(User[int]):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user_string(self) -> UserString:
            return UserString(id=1, data="hello", name="test")

        @strawberry.field
        def get_user_int(self) -> UserInt:
            return UserInt(id=2, data=42, name="test")

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Query {
  getUserString: UserString!
  getUserInt: UserInt!
}

type UserInt {
  id: Int!
  data: Int!
  name: String!
}

type UserString {
  id: Int!
  data: String!
  name: String!
}\
""")


def test_can_convert_generic_alias_fields_to_strawberry():
    @strawberry.pydantic.type
    class Test(pydantic.BaseModel):
        list_1d: list[int]
        list_2d: list[list[int]]

    fields = get_object_definition(Test, strict=True).fields
    assert isinstance(fields[0].type, StrawberryList)
    assert isinstance(fields[1].type, StrawberryList)


def test_can_convert_optional_union_type_expression_fields_to_strawberry():
    @strawberry.pydantic.type
    class Test(pydantic.BaseModel):
        optional_list: list[int] | None
        optional_str: str | None

    fields = get_object_definition(Test, strict=True).fields
    assert isinstance(fields[0].type, StrawberryOptional)
    assert isinstance(fields[1].type, StrawberryOptional)


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str


@strawberry.pydantic.type
class Post(pydantic.BaseModel):
    title: str


@strawberry.pydantic.type
class Page(pydantic.BaseModel, Generic[T]):
    items: list[T]
    total: int

    @strawberry.pydantic.field
    def first(self) -> T | None:
        return self.items[0] if self.items else None


def test_parametrized_generic_models_are_graphql_types():
    @strawberry.pydantic.type
    class Directory(pydantic.BaseModel):
        users: Page[User]

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self) -> Page[User]:
            return Page[User](items=[User(name="Ada")], total=1)

        @strawberry.field
        def posts(self) -> Page[Post]:
            return Page[Post](items=[], total=0)

        @strawberry.field
        def directory(self) -> Directory:
            return Directory(users=Page[User](items=[], total=0))

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Directory {
  users: UserPage!
}

type Post {
  title: String!
}

type PostPage {
  items: [Post!]!
  total: Int!
  first: Post
}

type Query {
  users: UserPage!
  posts: PostPage!
  directory: Directory!
}

type User {
  name: String!
}

type UserPage {
  items: [User!]!
  total: Int!
  first: User
}\
""")

    result = schema.execute_sync(
        "{ users { total items { name } first { name } } posts { first { title } } }"
    )

    assert not result.errors
    assert result.data == {
        "users": {"total": 1, "items": [{"name": "Ada"}], "first": {"name": "Ada"}},
        "posts": {"first": None},
    }


def test_instances_of_the_generic_model_can_be_returned():
    @strawberry.type
    class Query:
        @strawberry.field
        def users(self) -> Page[User]:
            return Page(items=[User(name="Ada")], total=1)

        @strawberry.field
        def search(self) -> Page[User] | Page[Post]:
            return Page(items=[Post(title="Hi")], total=1)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ users { items { name } } search { __typename } }")

    assert not result.errors
    assert result.data == {
        "users": {"items": [{"name": "Ada"}]},
        "search": {"__typename": "PostPage"},
    }


def test_nested_parametrized_generic_models():
    @strawberry.pydantic.type
    class Edge(pydantic.BaseModel, Generic[T]):
        node: T

    U = TypeVar("U")

    @strawberry.pydantic.type
    class Section(pydantic.BaseModel, Generic[U]):
        page: Page[U]

    @strawberry.type
    class Query:
        @strawberry.field
        def edges(self) -> Page[Edge[User]]:
            return Page[Edge[User]](items=[Edge[User](node=User(name="Ada"))], total=1)

        @strawberry.field
        def section(self) -> Section[Post]:
            return Section[Post](page=Page[Post](items=[], total=0))

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Post {
  title: String!
}

type PostPage {
  items: [Post!]!
  total: Int!
  first: Post
}

type PostSection {
  page: PostPage!
}

type Query {
  edges: UserEdgePage!
  section: PostSection!
}

type User {
  name: String!
}

type UserEdge {
  node: User!
}

type UserEdgePage {
  items: [UserEdge!]!
  total: Int!
  first: UserEdge
}\
""")

    result = schema.execute_sync("{ edges { first { node { name } } } }")

    assert not result.errors
    assert result.data == {"edges": {"first": {"node": {"name": "Ada"}}}}


def test_self_referencing_parametrized_generic_models_raise_an_error():
    @strawberry.pydantic.type
    class Tree(pydantic.BaseModel, Generic[T]):
        value: T
        children: list["Tree[T]"] = []

    # the type of the field is resolved when `Query` is decorated
    with pytest.raises(TypeError) as exc_info:

        @strawberry.type
        class Query:
            tree: Tree[int]

    assert str(exc_info.value) == (
        "`Tree[int].children` references a parametrized generic model while it's "
        "created, like `children: list[Tree[T]]` in a `Tree[T]`, which isn't "
        "supported yet"
    )


def test_parametrized_generic_inputs():
    received: list[object] = []

    @strawberry.pydantic.input
    class Filter(pydantic.BaseModel, Generic[T]):
        value: T

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: Filter[int]) -> bool:
            received.append(filter)

            return True

    schema = strawberry.Schema(query=Query)

    assert "input IntFilter {\n  value: Int!\n}" in str(schema)

    result = schema.execute_sync("{ search(filter: {value: 1}) }")

    assert not result.errors
    assert received == [Filter[int](value=1)]
    assert type(received[0]) is Filter[int]


def test_parametrized_generic_interfaces():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel, Generic[T]):
        value: T

    @strawberry.pydantic.type
    class AdaNode(Node[User]):
        version: int

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self) -> Node[User]:
            return AdaNode(value=User(name="Ada"), version=1)

    schema = strawberry.Schema(query=Query, types=[AdaNode])

    assert str(schema) == snapshot("""\
type AdaNode implements UserNode {
  value: User!
  version: Int!
}

type Query {
  node: UserNode!
}

type User {
  name: String!
}

interface UserNode {
  value: User!
}\
""")

    result = schema.execute_sync(
        "{ node { __typename value { name } ... on AdaNode { version } } }"
    )

    assert not result.errors
    assert result.data == {
        "node": {"__typename": "AdaNode", "value": {"name": "Ada"}, "version": 1}
    }


def test_parametrized_generic_models_keep_the_options_of_their_generic_model():
    @strawberry.pydantic.type(
        name="Paginated", description="A page of items", include_computed=False
    )
    class Paginated(pydantic.BaseModel, Generic[T]):
        items: list[T]

        @pydantic.computed_field
        @property
        def count(self) -> int:
            return len(self.items)

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self) -> Paginated[User]:
            return Paginated[User](items=[])

    assert str(strawberry.Schema(query=Query)) == snapshot('''\
type Query {
  users: UserPaginated!
}

type User {
  name: String!
}

"""A page of items"""
type UserPaginated {
  items: [User!]!
}\
''')


def test_parametrized_generic_models_cant_be_decorated():
    with pytest.raises(TypeError) as exc_info:
        strawberry.pydantic.type(Page[Post])

    assert str(exc_info.value) == (
        "`Page[Post]` is a parametrized generic model, which can't be decorated: "
        "decorate `Page` instead, which makes `Page[Post]` a GraphQL type too, or a "
        "subclass of `Page[Post]` to give it a name of its own"
    )


def test_parametrized_generic_query_is_specialized_on_first_use():
    @strawberry.pydantic.type
    class Box(pydantic.BaseModel, Generic[T]):
        value: T

    schema = strawberry.Schema(query=Box[int])
    result = schema.execute_sync("{ value }", root_value=Box[int](value=7))

    assert not result.errors
    assert result.data == {"value": 7}
    assert "value: Int!" in str(schema)


def test_lazy_generic_union_members_are_specialized(monkeypatch):
    @strawberry.pydantic.type
    class Box(pydantic.BaseModel, Generic[T]):
        value: T

    monkeypatch.setattr(__name__ + ".LazyBox", Box[User], raising=False)

    @strawberry.type
    class Query:
        item: Annotated["LazyBox", strawberry.lazy(__name__)] | Post  # noqa: F821

    schema = strawberry.Schema(query=Query)

    assert "union UserBoxPost = UserBox | Post" in str(schema)


def test_federation_finds_entities_through_generic_additional_types():
    from strawberry.federation.schema_directives import Key

    @strawberry.pydantic.type(directives=[Key(fields="id")])
    class Product(pydantic.BaseModel):
        id: strawberry.ID

    @strawberry.pydantic.type
    class Box(pydantic.BaseModel, Generic[T]):
        value: T

    @strawberry.type
    class Query:
        hello: str = "world"

    schema = strawberry.federation.Schema(query=Query, types=[Box[Product]])

    assert "union _Entity = Product" in str(schema)
