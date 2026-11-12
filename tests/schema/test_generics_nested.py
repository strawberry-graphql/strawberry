import textwrap
from typing import Generic, TypeVar

import strawberry
from strawberry.scalars import JSON


def test_support_nested_generics():
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edge: Edge[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self) -> Connection[User]:
            return Connection(edge=Edge(node=User(name="Patrick")))

    schema = strawberry.Schema(query=Query)

    query = """{
        users {
            __typename
            edge {
                __typename
                node {
                    name
                }
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "users": {
            "__typename": "UserConnection",
            "edge": {"__typename": "UserEdge", "node": {"name": "Patrick"}},
        }
    }


def test_unions_nested_inside_a_list():
    T = TypeVar("T")

    @strawberry.type
    class JsonBlock:
        data: JSON

    @strawberry.type
    class BlockRowtype(Generic[T]):
        total: int
        items: list[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def blocks(
            self,
        ) -> list[BlockRowtype[int] | BlockRowtype[str] | JsonBlock]:
            return [
                BlockRowtype(total=3, items=["a", "b", "c"]),
                BlockRowtype(total=1, items=[1, 2, 3, 4]),
                JsonBlock(data=JSON({"a": 1})),
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """query {
        blocks {
            __typename
            ... on IntBlockRowtype {
                a: items
            }
            ... on StrBlockRowtype {
                b: items
            }
            ... on JsonBlock {
                data
            }
        }
    }"""
    )

    assert not result.errors

    assert result.data == {
        "blocks": [
            {"__typename": "StrBlockRowtype", "b": ["a", "b", "c"]},
            {"__typename": "IntBlockRowtype", "a": [1, 2, 3, 4]},
            {"__typename": "JsonBlock", "data": {"a": 1}},
        ]
    }


def test_unions_nested_inside_a_list_with_no_items():
    T = TypeVar("T")

    @strawberry.type
    class JsonBlock:
        data: JSON

    @strawberry.type
    class BlockRowtype(Generic[T]):
        total: int
        items: list[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def blocks(
            self,
        ) -> list[BlockRowtype[int] | BlockRowtype[str] | JsonBlock]:
            return [
                BlockRowtype(total=3, items=[]),
                BlockRowtype(total=1, items=[]),
                JsonBlock(data=JSON({"a": 1})),
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """query {
        blocks {
            __typename
            ... on IntBlockRowtype {
                a: items
            }
            ... on StrBlockRowtype {
                b: items
            }
            ... on JsonBlock {
                data
            }
        }
    }"""
    )

    assert not result.errors

    assert result.data == {
        "blocks": [
            {"__typename": "IntBlockRowtype", "a": []},
            {"__typename": "IntBlockRowtype", "a": []},
            {"__typename": "JsonBlock", "data": {"a": 1}},
        ]
    }


def test_unions_nested_inside_a_list_of_lists():
    T = TypeVar("T")

    @strawberry.type
    class JsonBlock:
        data: JSON

    @strawberry.type
    class BlockRowtype(Generic[T]):
        total: int
        items: list[list[T]]

    @strawberry.type
    class Query:
        @strawberry.field
        def blocks(
            self,
        ) -> list[BlockRowtype[int] | BlockRowtype[str] | JsonBlock]:
            return [
                BlockRowtype(total=3, items=[["a", "b", "c"]]),
                BlockRowtype(total=1, items=[[1, 2, 3, 4]]),
                JsonBlock(data=JSON({"a": 1})),
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """query {
        blocks {
            __typename
            ... on IntBlockRowtype {
                a: items
            }
            ... on StrBlockRowtype {
                b: items
            }
            ... on JsonBlock {
                data
            }
        }
    }"""
    )

    assert not result.errors

    assert result.data == {
        "blocks": [
            {"__typename": "StrBlockRowtype", "b": [["a", "b", "c"]]},
            {"__typename": "IntBlockRowtype", "a": [[1, 2, 3, 4]]},
            {"__typename": "JsonBlock", "data": {"a": 1}},
        ]
    }


def test_using_generics_with_an_interface():
    T = TypeVar("T")

    @strawberry.interface
    class BlockInterface:
        id: strawberry.ID
        disclaimer: str | None = strawberry.field(default=None)

    @strawberry.type
    class JsonBlock(BlockInterface):
        data: JSON

    @strawberry.type
    class BlockRowtype(BlockInterface, Generic[T]):
        total: int
        items: list[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def blocks(self) -> list[BlockInterface]:
            return [
                BlockRowtype(id=strawberry.ID("3"), total=3, items=["a", "b", "c"]),
                BlockRowtype(id=strawberry.ID("1"), total=1, items=[1, 2, 3, 4]),
                JsonBlock(id=strawberry.ID("2"), data=JSON({"a": 1})),
            ]

    schema = strawberry.Schema(
        query=Query, types=[BlockRowtype[int], JsonBlock, BlockRowtype[str]]
    )

    expected_schema = textwrap.dedent(
        '''
        interface BlockInterface {
          id: ID!
          disclaimer: String
        }

        type IntBlockRowtype implements BlockInterface {
          id: ID!
          disclaimer: String
          total: Int!
          items: [Int!]!
        }

        """
        The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf).
        """
        scalar JSON @specifiedBy(url: "https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf")

        type JsonBlock implements BlockInterface {
          id: ID!
          disclaimer: String
          data: JSON!
        }

        type Query {
          blocks: [BlockInterface!]!
        }

        type StrBlockRowtype implements BlockInterface {
          id: ID!
          disclaimer: String
          total: Int!
          items: [String!]!
        }
    '''
    ).strip()

    assert str(schema) == expected_schema

    result = schema.execute_sync(
        """query {
        blocks {
            id
            __typename
            ... on IntBlockRowtype {
                a: items
            }
            ... on StrBlockRowtype {
                b: items
            }
            ... on JsonBlock {
                data
            }
        }
    }"""
    )

    assert not result.errors

    assert result.data == {
        "blocks": [
            {"id": "3", "__typename": "StrBlockRowtype", "b": ["a", "b", "c"]},
            {"id": "1", "__typename": "IntBlockRowtype", "a": [1, 2, 3, 4]},
            {"id": "2", "__typename": "JsonBlock", "data": {"a": 1}},
        ]
    }


def test_supports_generic_in_unions_with_nesting():
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edge: Edge[T]

    @strawberry.type
    class Fallback:
        node: str

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self) -> Connection[User] | Fallback:
            return Connection(edge=Edge(node=User(name="Patrick")))

    schema = strawberry.Schema(query=Query)

    query = """{
        users {
            __typename
            ... on UserConnection {
                edge {
                    __typename
                    node {
                        name
                    }
                }
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "users": {
            "__typename": "UserConnection",
            "edge": {"__typename": "UserEdge", "node": {"name": "Patrick"}},
        }
    }


def test_does_not_raise_duplicated_type_error():
    T = TypeVar("T")

    @strawberry.type
    class Wrapper(Generic[T]):
        value: T

    @strawberry.type
    class Query:
        a: Wrapper[Wrapper[int]]
        b: Wrapper[Wrapper[int]]

    schema = strawberry.Schema(query=Query)

    expected_schema = textwrap.dedent(
        """
        type IntWrapper {
          value: Int!
        }

        type IntWrapperWrapper {
          value: IntWrapper!
        }

        type Query {
          a: IntWrapperWrapper!
          b: IntWrapperWrapper!
        }
    """
    ).strip()
    assert str(schema) == expected_schema


def test_generic_using_a_generic_with_another_type_parameter():
    T = TypeVar("T")
    S = TypeVar("S")

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[S]):
        edges: list[Edge[S]]
        last_edge: Edge[S]

        @strawberry.field
        def first_edge(self) -> Edge[S]:
            return self.edges[0]

    @strawberry.type
    class Query:
        @strawberry.field
        def connection(self) -> Connection[int]:
            return Connection(
                edges=[Edge(node=1), Edge(node=2)], last_edge=Edge(node=2)
            )

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type IntConnection {
      edges: [IntEdge!]!
      lastEdge: IntEdge!
      firstEdge: IntEdge!
    }

    type IntEdge {
      node: Int!
    }

    type Query {
      connection: IntConnection!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync(
        "{ connection { edges { node } lastEdge { node } firstEdge { node } } }"
    )

    assert not result.errors
    assert result.data == {
        "connection": {
            "edges": [{"node": 1}, {"node": 2}],
            "lastEdge": {"node": 2},
            "firstEdge": {"node": 1},
        }
    }


# types using themselves need to be declared at the module level, so that their
# forward references can be resolved

T = TypeVar("T")
S = TypeVar("S")


@strawberry.type
class TreeNode(Generic[T]):
    value: T
    children: list["TreeNode[T]"]


@strawberry.type
class Category(Generic[T]):
    # the field using the type comes before the one using its type parameter
    parent: "Category[T] | None"
    item: T


@strawberry.type
class Author(Generic[T]):
    id: T
    books: list["Book[T]"]


@strawberry.type
class Book(Generic[T]):
    id: T
    author: Author[T]


@strawberry.type
class Pair(Generic[T, S]):
    first: T
    second: S
    swapped: "Pair[S, T] | None"


@strawberry.input
class Condition(Generic[T]):
    fields: T | None = None
    conditions: list["Condition[T]"] = strawberry.field(default_factory=list)


def test_generic_type_using_itself():
    @strawberry.type
    class Query:
        @strawberry.field
        def int_tree(self) -> TreeNode[int]:
            return TreeNode(
                value=1,
                children=[TreeNode(value=2, children=[TreeNode(value=3, children=[])])],
            )

        @strawberry.field
        def str_tree(self) -> TreeNode[str]:
            return TreeNode(value="a", children=[])

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type IntTreeNode {
      value: Int!
      children: [IntTreeNode!]!
    }

    type Query {
      intTree: IntTreeNode!
      strTree: StrTreeNode!
    }

    type StrTreeNode {
      value: String!
      children: [StrTreeNode!]!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync(
        """
        {
          intTree { value children { value children { value children { value } } } }
          strTree { value children { value } }
        }
        """
    )

    assert not result.errors
    assert result.data == {
        "intTree": {
            "value": 1,
            "children": [{"value": 2, "children": [{"value": 3, "children": []}]}],
        },
        "strTree": {"value": "a", "children": []},
    }


def test_generic_type_using_itself_before_its_type_parameter():
    @strawberry.type
    class Query:
        @strawberry.field
        def category(self) -> Category[str]:
            return Category(item="child", parent=Category(item="root", parent=None))

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Query {
      category: StrCategory!
    }

    type StrCategory {
      parent: StrCategory
      item: String!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync(
        "{ category { item parent { item parent { item } } } }"
    )

    assert not result.errors
    assert result.data == {
        "category": {"item": "child", "parent": {"item": "root", "parent": None}}
    }


def test_generic_types_using_each_other():
    @strawberry.type
    class Query:
        @strawberry.field
        def author(self) -> Author[int]:
            author = Author(id=1, books=[])
            author.books.append(Book(id=2, author=author))
            return author

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type IntAuthor {
      id: Int!
      books: [IntBook!]!
    }

    type IntBook {
      id: Int!
      author: IntAuthor!
    }

    type Query {
      author: IntAuthor!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync("{ author { id books { id author { id } } } }")

    assert not result.errors
    assert result.data == {
        "author": {"id": 1, "books": [{"id": 2, "author": {"id": 1}}]}
    }


def test_generic_type_using_itself_with_swapped_type_parameters():
    @strawberry.type
    class Query:
        @strawberry.field
        def pair(self) -> Pair[int, str]:
            return Pair(
                first=1, second="a", swapped=Pair(first="a", second=1, swapped=None)
            )

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type IntStrPair {
      first: Int!
      second: String!
      swapped: StrIntPair
    }

    type Query {
      pair: IntStrPair!
    }

    type StrIntPair {
      first: String!
      second: Int!
      swapped: IntStrPair
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync(
        "{ pair { first second swapped { first second swapped { first } } } }"
    )

    assert not result.errors
    assert result.data == {
        "pair": {
            "first": 1,
            "second": "a",
            "swapped": {"first": "a", "second": 1, "swapped": None},
        }
    }


def test_generic_type_using_itself_with_swapped_container_type_parameters():
    # list[int] and int | None wrap the same type, but they are different
    # arguments, so the swapped pair is a different type
    @strawberry.type
    class Query:
        @strawberry.field
        def pair(self) -> Pair[list[int], int | None]:
            return Pair(
                first=[1], second=None, swapped=Pair(first=2, second=[3], swapped=None)
            )

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type IntListIntOptionalPair {
      first: [Int!]!
      second: Int
      swapped: IntOptionalIntListPair
    }

    type IntOptionalIntListPair {
      first: Int
      second: [Int!]!
      swapped: IntListIntOptionalPair
    }

    type Query {
      pair: IntListIntOptionalPair!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync("{ pair { first second swapped { first second } } }")

    assert not result.errors
    assert result.data == {
        "pair": {"first": [1], "second": None, "swapped": {"first": 2, "second": [3]}}
    }


def test_generic_input_using_itself():
    @strawberry.input
    class UserFilter:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def matches(self, where: Condition[UserFilter]) -> list[str]:
            return [condition.fields.name for condition in where.conditions]

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Query {
      matches(where: UserFilterCondition!): [String!]!
    }

    input UserFilter {
      name: String!
    }

    input UserFilterCondition {
      fields: UserFilter = null
      conditions: [UserFilterCondition!]! = []
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync(
        """
        {
          matches(
            where: { conditions: [{ fields: { name: "Ada" } }, { fields: { name: "Grace" } }] }
          )
        }
        """
    )

    assert not result.errors
    assert result.data == {"matches": ["Ada", "Grace"]}
