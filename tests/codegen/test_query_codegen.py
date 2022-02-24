# TODO:
# 1. test anonymous operations
# 2. test fragments
# 3. test variables
# 7. test input objects
# 13. test mutations (raise?)
# 14. test subscriptions (raise)
# 16. plugins for output

import textwrap

from strawberry.codegen import QueryCodegen
from strawberry.codegen.plugins.python import PythonPlugin


# TODO: add id back in


def test_codegen_basic(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

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


def test_list_and_optional(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

    input_query = """
    query OperationName {
        optionalInt
        listOfInt
        listOfOptionalInt
    }
    """

    expected_output = """
    from typing import List, Optional

    class OperationNameResult:
        optional_int: Optional[int]
        list_of_int: List[int]
        list_of_optional_int: List[Optional[int]]
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_multiple_types(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

    input_query = """
    query OperationName {
        person {
            name
        }
        listOfPeople {
            name
        }
    }
    """

    expected_output = """
    from typing import List

    class OperationNameResultPerson:
        name: str

    class OperationNameResultListOfPeople:
        name: str

    class OperationNameResult:
        person: OperationNameResultPerson
        list_of_people: List[OperationNameResultListOfPeople]
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_multiple_types_optional(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

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


def test_enum(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

    input_query = """
    query OperationName {
        enum
    }
    """

    expected_output = """
    from enum import Enum

    class Color(Enum):
        RED = "RED"
        GREEN = "GREEN"
        BLUE = "BLUE"

    class OperationNameResult:
        enum: Color
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_scalar(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

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


def test_union(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

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

    OperationNameResultUnion = Union[OperationNameResultUnionAnimal, OperationNameResultUnionPerson]

    class OperationNameResult:
        union: OperationNameResultUnion
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_interface(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

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


def test_interface_fragment_single_fragment(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

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
        interface: OperationNameResultInterfaceBlogPost
    """

    # TODO: do we need the verbosity here?

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_interface_fragment(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

    input_query = """
    query OperationName {
        interface {
            id

            ... on BlogPost {
                title
            }

            ... on Image {
                url
            }
        }
    }
    """

    expected_output = """
    from typing import Union

    class OperationNameResultInterfaceBlogPost:
        id: str
        title: str

    class OperationNameResultInterfaceImage:
        id: str
        url: str

    OperationNameResultInterface = Union[OperationNameResultInterfaceBlogPost, OperationNameResultInterfaceImage]

    class OperationNameResult:
        interface: OperationNameResultInterface
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()
