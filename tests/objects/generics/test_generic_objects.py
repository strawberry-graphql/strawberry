import datetime
import timeit
from typing import Generic, List, Optional, TypeVar, Union

import pytest

import strawberry
from strawberry.exceptions import MissingTypesForGenericError
from strawberry.type import StrawberryList, StrawberryOptional
from strawberry.types.types import (
    TemplateTypeDefinition,
    TypeDefinition,
    get_type_definition as base_get_get_type_definition,
)
from strawberry.union import StrawberryUnion


T = TypeVar("T")


def get_type_definition(type_: type) -> TypeDefinition:
    ret = base_get_get_type_definition(type_)
    assert isinstance(ret, TypeDefinition)
    assert not isinstance(ret, TemplateTypeDefinition)
    return ret


def get_template_definitions(type_: type) -> TemplateTypeDefinition:
    res = base_get_get_type_definition(type_)
    assert isinstance(res, TemplateTypeDefinition)
    return res


def test_basic_generic():
    @strawberry.type
    class Edge(Generic[T]):
        node_field: T

    definition = get_template_definitions(Edge)
    assert definition.is_generic
    assert definition.parameters == (T,)
    generated = Edge[int]
    generated_def = get_type_definition(generated)
    assert not generated_def.is_generic
    field = generated_def.fields[0]
    assert field.python_name == "node_field"
    assert field.type is int


def test_caches_generated():
    @strawberry.type
    class Edge(Generic[T]):
        node_field: T

    definition = get_template_definitions(Edge)
    args = (int,)
    signature = hash(args)
    # equivalent to Edge[int] handled by StrawberryMeta.
    generated = definition.generate(args)
    assert definition.implementations[signature] is generated


def test_wont_generate_twice():
    @strawberry.type
    class Edge(Generic[T]):
        node_field: T

    definition = get_template_definitions(Edge)
    args = (int,)
    signature = hash(args)

    def generator():
        return definition.generate(args)

    first = timeit.timeit(generator, number=50)
    second = timeit.timeit(generator, number=50)
    assert second < first
    generated = definition.generate(args)
    assert definition.implementations[signature] is generated


def test_generics_nested():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edge: Edge[T]

    definition = get_template_definitions(Connection)
    assert definition.parameters == (T,)

    generated = Connection[int]
    generated_def = get_type_definition(generated)
    assert not generated_def.is_generic
    field = generated_def.fields[0]
    assert field.python_name == "edge"
    new_edge = get_type_definition(field.type)
    assert isinstance(new_edge, TypeDefinition)
    assert not new_edge.is_generic
    assert new_edge.fields[0].type is int


def test_generics_name():
    @strawberry.type(name="AnotherName")
    class EdgeName:
        node: str

    @strawberry.type
    class Connection(Generic[T]):
        edge: T

    definition = get_template_definitions(Connection)

    generated = definition.generate((EdgeName,))
    generated_def = get_type_definition(generated)
    assert not generated_def.is_generic
    field = generated_def.fields[0]
    assert field.python_name == "edge"
    new_edge = get_type_definition(field.type)
    assert new_edge.name == "AnotherName"


def test_generics_nested_in_list():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edges: List[Edge[T]]

    generated = Connection[str]
    generated_def = get_type_definition(generated)
    assert not generated_def.is_generic
    field = generated_def.fields[0]
    assert field.python_name == "edges"
    assert isinstance(field.type, StrawberryList)
    assert get_type_definition(field.type.of_type).fields[0].type is str


def test_list_inside_generic():
    T = TypeVar("T")

    @strawberry.type
    class Value(Generic[T]):
        valuation_date: datetime.date
        value: T

    @strawberry.type
    class Foo:
        string: Value[str]
        strings: Value[List[str]]
        optional_string: Value[Optional[str]]
        optional_strings: Value[Optional[List[str]]]

    definition = get_type_definition(Foo)
    assert not definition.is_generic
    [
        string_field,
        string_optional_field,
        optional_string_field,
        optional_list_strings_field,
    ] = definition.fields
    assert string_field.python_name == "string"
    assert string_field.type._type_definition.fields[1].type is str
    assert string_optional_field.python_name == "strings"
    assert string_optional_field.type._type_definition.fields[1].type.of_type is str
    assert optional_string_field.python_name == "optional_string"
    assert string_field.type._type_definition.fields[1].type is str
    assert optional_list_strings_field.python_name == "optional_strings"
    assert (
        optional_list_strings_field.type._type_definition.fields[1].type.of_type.of_type
        is str
    )


def test_generic_with_optional():
    @strawberry.type
    class Edge(Generic[T]):
        node: Optional[T]

    definition = get_type_definition(Edge[float])
    [field] = definition.fields
    assert field.python_name == "node"
    assert isinstance(field.type, StrawberryOptional)
    assert field.type.of_type is float


def test_generic_with_list():
    @strawberry.type
    class Connection(Generic[T]):
        edges: List[T]

    definition = get_type_definition(Connection[str])
    [field] = definition.fields
    assert field.python_name == "edges"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is str


def test_generic_with_list_of_optionals():
    @strawberry.type
    class Connection(Generic[T]):
        edges: List[Optional[T]]

    definition = get_type_definition(Connection[str])
    [field] = definition.fields
    assert field.python_name == "edges"
    assert isinstance(field.type, StrawberryList)
    assert isinstance(field.type.of_type, StrawberryOptional)
    assert field.type.of_type.of_type is str


def test_generics_with_unions():
    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: Union[Error, T]

    @strawberry.type
    class Node:
        name: str

    definition = get_type_definition(Edge[Node])
    [field] = definition.fields
    assert field.python_name == "node"
    assert isinstance(field.type, StrawberryUnion)
    assert field.type.types == (Error, Node)


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

    [field] = definition.fields
    assert field.python_name == "user"

    user_edge_definition = field.type._type_definition
    assert not user_edge_definition.is_generic

    [node_field] = user_edge_definition.fields
    assert node_field.python_name == "node"
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

    query_definition = get_type_definition(Query)

    [user_field] = query_definition.fields
    assert user_field.python_name == "users"

    user_connection_definition = get_type_definition(user_field.type)
    assert not user_connection_definition.is_generic

    edges_field = user_connection_definition.fields[0]
    assert edges_field.python_name == "edges"
    assert get_type_definition(edges_field.type).fields[0].type is User


def test_using_generics_raises_when_missing_annotation():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class User:
        name: str

    error_message = f'The type "{repr(Edge)}" is generic, but no type has been passed'
    with pytest.raises(MissingTypesForGenericError, match=error_message):

        @strawberry.type
        class Query:
            user: Edge


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
        f'The type "{repr(Connection)}" is generic, but no type has been passed'
    )
    with pytest.raises(MissingTypesForGenericError, match=error_message):

        @strawberry.type
        class Query:
            users: Connection


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

    query_definition = get_type_definition(Query)
    field = query_definition.fields[0]
    assert field.python_name == "user"
    assert isinstance(field.type, StrawberryOptional)
    assert get_type_definition(field.type.of_type).fields[0].type is str


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

    query_definition = get_type_definition(Query)
    field = query_definition.fields[0]
    assert field.python_name == "user"
    assert isinstance(field.type, StrawberryList)
    assert get_type_definition(field.type.of_type).fields[0].type is str


def test_generics_inside_unions():
    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        user: Union[Edge[float], Error]

    query_definition = get_type_definition(Query)
    field = query_definition.fields[0]
    assert field.python_name == "user"
    assert isinstance(field.type, StrawberryUnion)
    [
        edge_case,
        error_case,
    ] = field.type.types
    assert get_type_definition(edge_case).fields[0].type is float
    assert get_type_definition(error_case).fields[0].type is str


def test_multiple_generics_inside_unions():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        user: Union[Edge[int], Edge[str]]

    query_definition = get_type_definition(Query)
    field = query_definition.fields[0]
    assert field.python_name == "user"
    assert isinstance(field.type, StrawberryUnion)
    [
        edge_int,
        edge_str,
    ] = field.type.types
    assert get_type_definition(edge_int).fields[0].type is int
    assert get_type_definition(edge_str).fields[0].type is str


def test_union_inside_generics():
    @strawberry.type
    class Dog:
        name: int

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

    query_definition = get_type_definition(Query)
    connection = query_definition.fields[0]
    assert connection.python_name == "connection"
    nodes = get_type_definition(connection.type).fields[0]
    cat_dog = nodes.type.of_type
    assert isinstance(cat_dog, StrawberryUnion)
    [
        dog,
        cat,
    ] = cat_dog.types
    assert get_type_definition(dog).fields[0].type is int
    assert get_type_definition(cat).fields[0].type is str


def test_anonymous_union_inside_generics():
    @strawberry.type
    class Dog:
        name: int

    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Connection(Generic[T]):
        nodes: List[T]

    @strawberry.type
    class Query:
        connection: Connection[Union[Dog, Cat]]

    query_definition = get_type_definition(Query)
    connection = query_definition.fields[0]
    nodes = get_type_definition(connection.type).fields[0]
    cat_dog = nodes.type.of_type
    assert isinstance(cat_dog, StrawberryUnion)
    [
        dog,
        cat,
    ] = cat_dog.types
    assert get_type_definition(dog).fields[0].type is int
    assert get_type_definition(cat).fields[0].type is str


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

    [user_field] = query_definition.fields
    assert user_field.python_name == "user"

    with_name_definition = user_field.type._type_definition
    assert not with_name_definition.is_generic

    [node_field] = with_name_definition.fields
    assert node_field.python_name == "node"
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

    query_definition = get_type_definition(Query)
    user_field = query_definition.fields[0]
    assert user_field.python_name == "user"
    post_collection_definition = get_type_definition(user_field.type)

    by_id_field = post_collection_definition.fields[0]
    assert by_id_field.python_name == "by_id"
    assert isinstance(by_id_field.type, StrawberryList)
    assert by_id_field.type.of_type is Post

    ids_argument = by_id_field.arguments[0]
    assert ids_argument.python_name == "ids"
    assert isinstance(ids_argument.type, StrawberryList)
    assert ids_argument.type.of_type is int


def test_federation():
    @strawberry.federation.type(keys=["id"])
    class Edge(Generic[T]):
        id: strawberry.ID
        node_field: T

    definition = get_type_definition(Edge[str])

    assert not definition.is_generic
    assert definition.directives == Edge._type_definition.directives

    [field1_copy, field2_copy] = definition.fields

    assert field1_copy.python_name == "id"
    assert field1_copy.type is strawberry.ID

    assert field2_copy.python_name == "node_field"
    assert field2_copy.type is str
