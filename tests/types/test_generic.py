from typing import Generic, List, Optional, TypeVar, Union

import pytest

import strawberry
from strawberry.exceptions import MissingTypesForGenericError
from strawberry.types.generics import copy_type_with
from strawberry.union import StrawberryUnion


T = TypeVar("T")


def test_basic_generic():
    @strawberry.type
    class Edge(Generic[T]):
        node_field: T

    definition = Edge._type_definition

    assert definition.name == "Edge"
    assert definition.is_generic
    assert definition.type_params == {"node_field": T}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "nodeField"
    assert definition.fields[0].type == T
    assert definition.fields[0].is_optional is False

    # let's make a copy of this generic type

    Copy = copy_type_with(Edge, str)

    definition = Copy._type_definition

    assert definition.name == "StrEdge"
    assert definition.is_generic is False
    assert definition.type_params == {}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "nodeField"
    assert definition.fields[0].type == str
    assert definition.fields[0].is_optional is False


def test_generics_nested():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edge: Edge[T]

    definition = Connection._type_definition

    assert definition.name == "Connection"
    assert definition.is_generic
    assert definition.type_params == {"edge": T}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "edge"
    assert definition.fields[0].type._type_definition.type_params == {"node": T}
    assert definition.fields[0].is_optional is False

    # let's make a copy of this generic type

    Copy = copy_type_with(Connection, str)

    definition = Copy._type_definition

    assert definition.name == "StrConnection"
    assert definition.is_generic is False
    assert definition.type_params == {}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "edge"
    assert definition.fields[0].type._type_definition.name == "StrEdge"
    assert definition.fields[0].is_optional is False


def test_generics_nested_in_list():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edges: List[Edge[T]]

    definition = Connection._type_definition

    assert definition.name == "Connection"
    assert definition.is_generic
    assert definition.type_params == {"edges": T}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "edges"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type._type_definition.type_params == {"node": T}

    # let's make a copy of this generic type

    Copy = copy_type_with(Connection, str)

    definition = Copy._type_definition

    assert definition.name == "StrConnection"
    assert definition.is_generic is False
    assert definition.type_params == {}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "edges"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type._type_definition.name == "StrEdge"


def test_generic_with_optional():
    @strawberry.type
    class Edge(Generic[T]):
        node: Optional[T]

    definition = Edge._type_definition

    assert definition.name == "Edge"
    assert definition.is_generic
    assert definition.type_params == {"node": T}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "node"
    assert definition.fields[0].type == T
    assert definition.fields[0].is_optional is True

    # let's make a copy of this generic type

    Copy = copy_type_with(Edge, str)

    definition = Copy._type_definition

    assert definition.name == "StrEdge"
    assert definition.is_generic is False
    assert definition.type_params == {}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "node"
    assert definition.fields[0].type == str
    assert definition.fields[0].is_optional is True


def test_generic_with_list():
    @strawberry.type
    class Connection(Generic[T]):
        edges: List[T]

    definition = Connection._type_definition

    assert definition.name == "Connection"
    assert definition.is_generic
    assert definition.type_params == {"edges": T}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "edges"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == T

    # let's make a copy of this generic type

    Copy = copy_type_with(Connection, str)

    definition = Copy._type_definition

    assert definition.name == "StrConnection"
    assert definition.is_generic is False
    assert definition.type_params == {}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "edges"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == str


def test_generic_with_list_of_optionals():
    @strawberry.type
    class Connection(Generic[T]):
        edges: List[Optional[T]]

    definition = Connection._type_definition

    assert definition.name == "Connection"
    assert definition.is_generic
    assert definition.type_params == {"edges": T}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "edges"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == T
    assert definition.fields[0].child.is_optional

    # let's make a copy of this generic type

    Copy = copy_type_with(Connection, str)

    definition = Copy._type_definition

    assert definition.name == "StrConnection"
    assert definition.is_generic is False
    assert definition.type_params == {}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "edges"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == str
    assert definition.fields[0].child.is_optional


def test_generics_with_unions():
    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: Union[Error, T]

    definition = Edge._type_definition

    assert definition.name == "Edge"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "node"
    assert isinstance(definition.fields[0].type, StrawberryUnion)
    assert definition.fields[0].type.types == (Error, T)

    assert definition.type_params == {"node": T}

    # let's make a copy of this generic type

    @strawberry.type
    class Node:
        name: str

    Copy = copy_type_with(Edge, Node)

    definition = Copy._type_definition

    assert definition.name == "NodeEdge"
    assert definition.is_generic is False
    assert definition.type_params == {}

    assert len(definition.fields) == 1

    assert definition.fields[0].name == "node"

    union_definition = definition.fields[0].type
    assert isinstance(union_definition, StrawberryUnion)
    assert union_definition.name == "ErrorNode"
    assert union_definition.types == (Error, Node)

    assert definition.fields[0].is_optional is False


def test_using_generics():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        user: Edge[User]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "user"
    assert definition.fields[0].type._type_definition.name == "UserEdge"
    assert definition.fields[0].type._type_definition.is_generic is False
    assert definition.fields[0].type._type_definition.fields[0].name == "node"
    assert definition.fields[0].type._type_definition.fields[0].type == User


def test_using_generics_nested():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edges: Edge[T]

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        users: Connection[User]

    definition = Connection._type_definition

    assert definition.is_generic
    assert definition.type_params == {"edges": T}

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "users"
    assert definition.fields[0].type._type_definition.name == "UserConnection"
    assert definition.fields[0].type._type_definition.is_generic is False
    assert definition.fields[0].type._type_definition.fields[0].name == "edges"
    assert (
        definition.fields[0].type._type_definition.fields[0].type._type_definition.name
        == "UserEdge"
    )


def test_using_generics_raises_when_missing_annotation():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class User:
        name: str

    error_message = (
        r'The type "Edge" of the field "user" is generic, but no type has been passed'
    )

    @strawberry.type
    class Query:
        user: Edge

    with pytest.raises(MissingTypesForGenericError, match=error_message):

        Query._type_definition.fields


def test_using_generics_raises_when_missing_annotation_nested():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edges: List[Edge[T]]

    @strawberry.type
    class User:
        name: str

    error_message = (
        'The type "Connection" of the field "users" is'
        " generic, but no type has been passed"
    )

    @strawberry.type
    class Query:
        users: Connection

    with pytest.raises(MissingTypesForGenericError, match=error_message):
        Query._type_definition.fields


def test_generics_inside_optional():
    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        user: Optional[Edge[str]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "user"
    assert definition.fields[0].type._type_definition.name == "StrEdge"
    assert definition.fields[0].type._type_definition.is_generic is False
    assert definition.fields[0].is_optional

    assert definition.type_params == {}


def test_generics_inside_list():
    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        user: List[Edge[str]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "user"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].is_list
    assert definition.fields[0].child.type._type_definition.name == "StrEdge"
    assert definition.fields[0].child.type._type_definition.is_generic is False

    assert definition.type_params == {}


def test_generics_inside_unions():
    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        user: Union[Edge[str], Error]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.type_params == {}
    assert definition.fields[0].name == "user"
    assert definition.fields[0].is_optional is False

    union_definition = definition.fields[0].type

    assert isinstance(union_definition, StrawberryUnion)
    assert union_definition.name == "StrEdgeError"
    assert union_definition.types[0]._type_definition.name == "StrEdge"
    assert union_definition.types[0]._type_definition.is_generic is False


def test_multiple_generics_inside_unions():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        user: Union[Edge[int], Edge[str]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.type_params == {}
    assert definition.fields[0].name == "user"
    assert definition.fields[0].is_optional is False

    union_definition = definition.fields[0].type

    assert isinstance(union_definition, StrawberryUnion)
    assert union_definition.name == "IntEdgeStrEdge"
    assert union_definition.types[0]._type_definition.name == "IntEdge"
    assert union_definition.types[0]._type_definition.is_generic is False
    assert union_definition.types[0]._type_definition.fields[0].type == int

    assert union_definition.types[1]._type_definition.name == "StrEdge"
    assert union_definition.types[1]._type_definition.is_generic is False
    assert union_definition.types[1]._type_definition.fields[0].type == str


def test_union_inside_generics():
    @strawberry.type
    class Dog:
        name: str

    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Connection(Generic[T]):
        nodes: List[T]

    DogCat = strawberry.union("DogCat", (Dog, Cat))

    @strawberry.type
    class Query:
        connection: Connection[DogCat]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.type_params == {}
    assert definition.fields[0].name == "connection"
    assert definition.fields[0].is_optional is False

    type_definition = definition.fields[0].type._type_definition

    assert type_definition.name == "DogCatConnection"
    assert len(type_definition.fields) == 1
    assert type_definition.fields[0].is_list is True

    union_definition = type_definition.fields[0].child.type

    assert isinstance(union_definition, StrawberryUnion)
    assert union_definition.types[0]._type_definition.name == "Dog"
    assert union_definition.types[1]._type_definition.name == "Cat"


def test_anonymous_union_inside_generics():
    @strawberry.type
    class Dog:
        name: str

    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Connection(Generic[T]):
        nodes: List[T]

    @strawberry.type
    class Query:
        connection: Connection[Union[Dog, Cat]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.type_params == {}
    assert definition.fields[0].name == "connection"
    assert definition.fields[0].is_optional is False

    type_definition = definition.fields[0].type._type_definition

    assert type_definition.name == "DogCatConnection"
    assert len(type_definition.fields) == 1
    assert type_definition.fields[0].is_list is True

    union_definition = type_definition.fields[0].child.type

    assert isinstance(union_definition, StrawberryUnion)
    assert union_definition.types[0]._type_definition.name == "Dog"
    assert union_definition.types[1]._type_definition.name == "Cat"


def test_using_generics_with_interfaces():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.interface
    class WithName:
        name: str

    @strawberry.type
    class Query:
        user: Edge[WithName]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "user"
    assert definition.fields[0].type._type_definition.name == "WithNameEdge"
    assert definition.fields[0].type._type_definition.is_generic is False
    assert definition.fields[0].type._type_definition.fields[0].name == "node"
    assert definition.fields[0].type._type_definition.fields[0].type == WithName
