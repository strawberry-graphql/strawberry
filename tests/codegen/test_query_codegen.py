# TODO:
# 1. test anonymous operations
# 2. test fragments
# 3. test variables
# 7. test input objects
# 13. test mutations (raise?)
# 14. test subscriptions (raise)
# 16. plugins for output


import enum
import textwrap
from typing import List, NewType, Optional

import strawberry
from strawberry.codegen import CodegenPlugin, QueryCodegen


JSON = strawberry.scalar(NewType("JSON", str))


@strawberry.enum
class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@strawberry.type
class Person:
    name: str
    age: int


@strawberry.type
class Animal:
    name: str
    age: int


PersonOrAnimal = strawberry.union("PersonOrAnimal", (Person, Animal))


@strawberry.interface
class Node:
    id: str


@strawberry.type
class BlogPost(Node):
    title: str


@strawberry.type
class Query:
    id: strawberry.ID
    integer: int
    another_integer: int
    optional_int: Optional[int]
    list_of_optional_int: List[Optional[int]]
    person: Person
    optional_person: Optional[Person]
    enum: Color
    json: JSON
    union: PersonOrAnimal
    interface: Node


schema = strawberry.Schema(query=Query, types=[BlogPost])


class PythonCodegenPlugin(CodegenPlugin):
    ...


def test_codegen_basic():
    generator = QueryCodegen(schema, plugins=[PythonCodegenPlugin])

    input_query = """
    query OperationName {
        id
        integer
        anotherInteger
    }
    """

    expected_output = """
    class OperationNameResult:
        id: str
        integer: int
        another_integer: int
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_list_and_optional():
    generator = QueryCodegen(schema, plugins=[PythonCodegenPlugin])

    input_query = """
    query OperationName {
        optionalInt
        listOfOptionalInt
    }
    """

    expected_output = """
    from typing import List, Optional

    class OperationNameResult:
        optional_int: Optional[int]
        list_of_optional_int: List[Optional[int]]
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_multiple_types():
    generator = QueryCodegen(schema, plugins=[PythonCodegenPlugin])

    input_query = """
    query OperationName {
        person {
            name
        }
    }
    """

    expected_output = """
    class OperationNameResultPerson:
        name: str

    class OperationNameResult:
        person: OperationNameResultPerson
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_multiple_types_optional():
    generator = QueryCodegen(schema, plugins=[PythonCodegenPlugin])

    input_query = """
    query OperationName {
        optionalPerson {
            name
        }
    }
    """

    expected_output = """
    from typing import Optional

    class OperationNameResultOptionalPerson:
        name: str

    class OperationNameResult:
        optional_person: Optional[OperationNameResultOptionalPerson]
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_enum():
    generator = QueryCodegen(schema, plugins=[PythonCodegenPlugin])

    input_query = """
    query OperationName {
        enum
    }
    """

    expected_output = """
    from enum import Enum

    class OperationNameResultEnum(Enum):
        red = "red"
        green = "green"
        blue = "blue"

    class OperationNameResult:
        enum: OperationNameResultEnum
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_scalar():
    generator = QueryCodegen(schema, plugins=[PythonCodegenPlugin])

    input_query = """
    query OperationName {
        json
    }
    """

    expected_output = """
    from typing import NewType

    JSON = NewType("JSON", str)

    class OperationNameResult:
        json: JSON
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_union():
    generator = QueryCodegen(schema, plugins=[PythonCodegenPlugin])

    input_query = """
    query OperationName {
        union {
            ... on Animal {
                age
            }
            ... on Person {
                name
            }
        }
    }
    """

    expected_output = """
    from typing import Union

    class OperationNameResultUnionAnimal:
        age: int

    class OperationNameResultUnionPerson:
        name: str

    class OperationNameResult:
        union: Union[OperationNameResultUnionAnimal, OperationNameResultUnionPerson]
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_interface():
    generator = QueryCodegen(schema, plugins=[PythonCodegenPlugin])

    input_query = """
    query OperationName {
        interface {
            id
        }
    }
    """

    expected_output = """
    class OperationNameResultInterface:
        id: str

    class OperationNameResult:
        interface: OperationNameResultInterface
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_interface_fragment():
    generator = QueryCodegen(schema, plugins=[PythonCodegenPlugin])

    input_query = """
    query OperationName {
        interface {
            id

            ... on BlogPost {
                title
            }
        }
    }
    """

    expected_output = """
    class OperationNameResultInterfaceBlogPost:
        id: str
        title: str

    class OperationNameResult:
        interface: OperationNameResultInterface
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()
