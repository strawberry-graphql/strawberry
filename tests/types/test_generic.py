from typing import Generic, List, Optional, TypeVar, Union

import pytest

import strawberry
from strawberry.exceptions import MissingTypesForGenericError
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryTypeVar
from strawberry.union import StrawberryUnion


T = TypeVar("T")


def test_basic_generic():
    @strawberry.type
    class Edge(Generic[T]):
        node_field: T

    definition = Edge._type_definition
    assert definition.name == "Edge"
    assert definition.is_generic
    assert definition.type_params == [T]

    [field] = definition.fields
    assert field.graphql_name == "nodeField"
    assert isinstance(field.type, StrawberryTypeVar)
    assert field.type.type_var is T

    # let's make a copy of this generic type
    definition_copy = Edge._type_definition.copy_with({T: str})

    assert definition_copy.name == "StrEdge"
    assert not definition_copy.is_generic
    assert definition_copy.type_params == []

    [field_copy] = definition_copy.fields
    assert field_copy.graphql_name == "nodeField"
    assert field_copy.type is str


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
    assert definition.type_params == [T]

    [field] = definition.fields
    assert field.graphql_name == "edge"
    assert field.type._type_definition.type_params == [T]

    # let's make a copy of this generic type
    definition_copy = Connection._type_definition.copy_with({T: str})

    assert definition_copy.name == "StrConnection"
    assert not definition_copy.is_generic
    assert definition_copy.type_params == []

    [field_copy] = definition_copy.fields
    assert field_copy.graphql_name == "edge"
    assert field_copy.type._type_definition.name == "StrEdge"


def test_generics_name():
    @strawberry.type(name="AnotherName")
    class EdgeName:
        node: str

    @strawberry.type
    class Connection(Generic[T]):
        edge: T

    definition_copy = Connection._type_definition.copy_with({T: EdgeName})

    assert definition_copy.name == "AnotherNameConnection"
    assert not definition_copy.is_generic
    assert definition_copy.type_params == []

    [field_copy] = definition_copy.fields
    assert field_copy.graphql_name == "edge"
    assert field_copy.type._type_definition.name == "AnotherName"


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
    assert definition.type_params == [T]

    [field] = definition.fields
    assert field.graphql_name == "edges"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type._type_definition.type_params == [T]

    # let's make a copy of this generic type
    definition_copy = Connection._type_definition.copy_with({T: str})

    assert definition_copy.name == "StrConnection"
    assert not definition_copy.is_generic
    assert definition_copy.type_params == []

    [field_copy] = definition_copy.fields
    assert field_copy.graphql_name == "edges"
    assert isinstance(field_copy.type, StrawberryList)
    assert field_copy.type.of_type._type_definition.name == "StrEdge"


def test_generic_with_optional():
    @strawberry.type
    class Edge(Generic[T]):
        node: Optional[T]

    definition = Edge._type_definition
    assert definition.name == "Edge"
    assert definition.is_generic
    assert definition.type_params == [T]

    [field] = definition.fields
    assert field.graphql_name == "node"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryTypeVar)
    assert field.type.of_type.type_var is T

    # let's make a copy of this generic type
    definition_copy = Edge._type_definition.copy_with({T: str})

    assert definition_copy.name == "StrEdge"
    assert not definition_copy.is_generic
    assert definition_copy.type_params == []

    [field_copy] = definition_copy.fields
    assert field_copy.graphql_name == "node"
    assert isinstance(field_copy.type, StrawberryOptional)
    assert field_copy.type.of_type is str


def test_generic_with_list():
    @strawberry.type
    class Connection(Generic[T]):
        edges: List[T]

    definition = Connection._type_definition
    assert definition.name == "Connection"
    assert definition.is_generic
    assert definition.type_params == [T]

    [field] = definition.fields
    assert field.graphql_name == "edges"
    assert isinstance(field.type, StrawberryList)
    assert isinstance(field.type.of_type, StrawberryTypeVar)
    assert field.type.of_type.type_var is T

    # let's make a copy of this generic type
    definition_copy = Connection._type_definition.copy_with({T: str})

    assert definition_copy.name == "StrConnection"
    assert not definition_copy.is_generic
    assert definition_copy.type_params == []

    [field_copy] = definition_copy.fields
    assert field_copy.graphql_name == "edges"
    assert isinstance(field_copy.type, StrawberryList)
    assert field_copy.type.of_type is str


def test_generic_with_list_of_optionals():
    @strawberry.type
    class Connection(Generic[T]):
        edges: List[Optional[T]]

    definition = Connection._type_definition
    assert definition.name == "Connection"
    assert definition.is_generic
    assert definition.type_params == [T]

    [field] = definition.fields
    assert field.graphql_name == "edges"
    assert isinstance(field.type, StrawberryList)
    assert isinstance(field.type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type, StrawberryTypeVar)
    assert field.type.of_type.of_type.type_var is T

    # let's make a copy of this generic type
    definition_copy = Connection._type_definition.copy_with({T: str})

    assert definition_copy.name == "StrConnection"
    assert not definition_copy.is_generic
    assert definition_copy.type_params == []

    [field_copy] = definition_copy.fields
    assert field_copy.graphql_name == "edges"
    assert isinstance(field_copy.type, StrawberryList)
    assert isinstance(field_copy.type.of_type, StrawberryOptional)
    assert field_copy.type.of_type.of_type is str


def test_generics_with_unions():
    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: Union[Error, T]

    definition = Edge._type_definition
    assert definition.name == "Edge"
    assert definition.type_params == [T]

    [field] = definition.fields
    assert field.graphql_name == "node"
    assert isinstance(field.type, StrawberryUnion)
    assert field.type.types == (Error, T)

    # let's make a copy of this generic type
    @strawberry.type
    class Node:
        name: str

    definition_copy = Edge._type_definition.copy_with({T: Node})

    assert definition_copy.name == "NodeEdge"
    assert not definition_copy.is_generic
    assert definition_copy.type_params == []

    [field_copy] = definition_copy.fields
    assert field_copy.graphql_name == "node"
    assert isinstance(field_copy.type, StrawberryUnion)
    assert field_copy.type.name == "ErrorNode"
    assert field_copy.type.types == (Error, Node)


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

    [field] = definition.fields
    assert field.graphql_name == "user"

    user_edge_definition = field.type._type_definition
    assert user_edge_definition.name == "UserEdge"
    assert not user_edge_definition.is_generic

    [node_field] = user_edge_definition.fields
    assert node_field.graphql_name == "node"
    assert node_field.type is User


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

    connection_definition = Connection._type_definition
    assert connection_definition.is_generic
    assert connection_definition.type_params == [T]

    query_definition = Query._type_definition
    assert query_definition.name == "Query"

    [user_field] = query_definition.fields
    assert user_field.graphql_name == "users"

    user_connection_definition = user_field.type._type_definition
    assert user_connection_definition.name == "UserConnection"
    assert not user_connection_definition.is_generic

    [edges_field] = user_connection_definition.fields
    assert edges_field.graphql_name == "edges"

    user_edge_definition = edges_field.type._type_definition
    assert user_edge_definition.name == "UserEdge"


def test_using_generics_raises_when_missing_annotation():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class User:
        name: str

    error_message = (
        'The type "Edge" of the field "user" is generic, but no type has been passed'
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
        'The type "Connection" of the field "users" is generic, but no type has been '
        "passed"
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

    query_definition = Query._type_definition
    assert query_definition.name == "Query"
    assert query_definition.type_params == []

    [field] = query_definition.fields
    assert field.graphql_name == "user"
    assert isinstance(field.type, StrawberryOptional)

    str_edge_definition = field.type.of_type._type_definition
    assert str_edge_definition.name == "StrEdge"
    assert not str_edge_definition.is_generic


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

    query_definition = Query._type_definition
    assert query_definition.name == "Query"
    assert query_definition.type_params == []

    [field] = query_definition.fields
    assert field.graphql_name == "user"
    assert isinstance(field.type, StrawberryList)

    str_edge_definition = field.type.of_type._type_definition
    assert str_edge_definition.name == "StrEdge"
    assert not str_edge_definition.is_generic


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

    query_definition = Query._type_definition
    assert query_definition.name == "Query"
    assert query_definition.type_params == []

    [field] = query_definition.fields
    assert field.graphql_name == "user"
    assert not isinstance(field.type, StrawberryOptional)

    union = field.type
    assert isinstance(union, StrawberryUnion)
    assert union.name == "StrEdgeError"
    assert union.types[0]._type_definition.name == "StrEdge"
    assert not union.types[0]._type_definition.is_generic


def test_multiple_generics_inside_unions():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        user: Union[Edge[int], Edge[str]]

    query_definition = Query._type_definition
    assert query_definition.name == "Query"
    assert query_definition.type_params == []

    [user_field] = query_definition.fields
    assert user_field.graphql_name == "user"
    assert not isinstance(user_field.type, StrawberryOptional)

    union = user_field.type
    assert isinstance(union, StrawberryUnion)
    assert union.name == "IntEdgeStrEdge"

    int_edge_definition = union.types[0]._type_definition
    assert int_edge_definition.name == "IntEdge"
    assert not int_edge_definition.is_generic
    assert int_edge_definition.fields[0].type is int

    str_edge_definition = union.types[1]._type_definition
    assert str_edge_definition.name == "StrEdge"
    assert not str_edge_definition.is_generic
    assert str_edge_definition.fields[0].type is str


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

    query_definition = Query._type_definition
    assert query_definition.name == "Query"
    assert query_definition.type_params == []

    [connection_field] = query_definition.fields
    assert connection_field.graphql_name == "connection"
    assert not isinstance(connection_field, StrawberryOptional)

    dog_cat_connection_definition = connection_field.type._type_definition
    assert dog_cat_connection_definition.name == "DogCatConnection"

    [node_field] = dog_cat_connection_definition.fields
    assert isinstance(node_field.type, StrawberryList)

    union = dog_cat_connection_definition.fields[0].type.of_type
    assert isinstance(union, StrawberryUnion)
    assert union.types[0]._type_definition.name == "Dog"
    assert union.types[1]._type_definition.name == "Cat"


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
    assert definition.type_params == []

    [connection_field] = definition.fields
    assert connection_field.graphql_name == "connection"

    dog_cat_connection_definition = connection_field.type._type_definition
    assert dog_cat_connection_definition.name == "DogCatConnection"

    [node_field] = dog_cat_connection_definition.fields
    assert isinstance(node_field.type, StrawberryList)

    union = node_field.type.of_type
    assert isinstance(union, StrawberryUnion)
    assert union.types[0]._type_definition.name == "Dog"
    assert union.types[1]._type_definition.name == "Cat"


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

    query_definition = Query._type_definition
    assert query_definition.name == "Query"

    [user_field] = query_definition.fields
    assert user_field.graphql_name == "user"

    with_name_definition = user_field.type._type_definition
    assert with_name_definition.name == "WithNameEdge"
    assert not with_name_definition.is_generic

    [node_field] = with_name_definition.fields
    assert node_field.graphql_name == "node"
    assert node_field.type is WithName


def test_generic_with_arguments():
    T = TypeVar("T")

    @strawberry.type
    class Collection(Generic[T]):
        @strawberry.field
        def by_id(self, ids: List[int]) -> List[T]:
            return []

    @strawberry.type
    class Post:
        name: str

    @strawberry.type
    class Query:
        user: Collection[Post]

    query_definition = Query._type_definition
    assert query_definition.name == "Query"

    [user_field] = query_definition.fields
    assert user_field.python_name == "user"

    post_collection_definition = user_field.type._type_definition
    assert post_collection_definition.name == "PostCollection"
    assert not post_collection_definition.is_generic

    [by_id_field] = post_collection_definition.fields
    assert by_id_field.graphql_name == "byId"
    assert isinstance(by_id_field.type, StrawberryList)
    assert by_id_field.type.of_type is Post

    [ids_argument] = by_id_field.arguments
    assert ids_argument.graphql_name == "ids"
    assert isinstance(ids_argument.type, StrawberryList)
    assert ids_argument.type.of_type is int


def test_federation():
    @strawberry.federation.type(keys=["id"])
    class Edge(Generic[T]):
        id: strawberry.ID
        node_field: T

    definition = Edge._type_definition

    definition_copy = Edge._type_definition.copy_with({T: str})

    assert definition_copy.name == "StrEdge"
    assert not definition_copy.is_generic
    assert definition_copy.type_params == []
    assert definition_copy.federation.keys == ["id"]
    assert not definition_copy.federation.extend

    [field1_copy, field2_copy] = definition_copy.fields

    assert field1_copy.graphql_name == "id"
    assert field1_copy.type is strawberry.ID

    assert field2_copy.graphql_name == "nodeField"
    assert field2_copy.type is str
