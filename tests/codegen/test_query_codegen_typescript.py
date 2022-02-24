import textwrap

from strawberry.codegen import QueryCodegen
from strawberry.codegen.plugins.typescript import TypeScriptPlugin


def test_codegen_basic(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

    input_query = """
    query OperationName {
        id
        integer
        anotherInteger
    }
    """

    expected_output = """
    type OperationNameResult = {
        id: string
        integer: number
        another_integer: number
    }
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_list_and_optional(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

    input_query = """
    query OperationName {
        optionalInt
        listOfInt
        listOfOptionalInt
    }
    """

    expected_output = """
    type OperationNameResult = {
        optional_int: number | undefined
        list_of_int: number[]
        list_of_optional_int: (number | undefined)[]
    }
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_multiple_types(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

    input_query = """
    query OperationName {
        person {
            name
        }
    }
    """

    expected_output = """
    type OperationNameResultPerson = {
        name: string
    }

    type OperationNameResult = {
        person: OperationNameResultPerson
    }
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_multiple_types_optional(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

    input_query = """
    query OperationName {
        optionalPerson {
            name
        }
    }
    """

    expected_output = """
    type OperationNameResultOptionalPerson = {
        name: string
    }

    type OperationNameResult = {
        optional_person: OperationNameResultOptionalPerson | undefined
    }
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_enum(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

    input_query = """
    query OperationName {
        enum
    }
    """

    expected_output = """
    enum Color {
        RED = "RED",
        GREEN = "GREEN",
        BLUE = "BLUE",
    }

    type OperationNameResult = {
        enum: Color
    }
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_scalar(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

    input_query = """
    query OperationName {
        json
    }
    """

    expected_output = """
    type JSON = string

    type OperationNameResult = {
        json: JSON
    }
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_union(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

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
    type OperationNameResultUnionAnimal = {
        age: number
    }

    type OperationNameResultUnionPerson = {
        name: string
    }

    type OperationNameResultUnion = OperationNameResultUnionAnimal | OperationNameResultUnionPerson

    type OperationNameResult = {
        union: OperationNameResultUnion
    }
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_interface(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

    input_query = """
    query OperationName {
        interface {
            id
        }
    }
    """

    expected_output = """
    type OperationNameResultInterface = {
        id: string
    }

    type OperationNameResult = {
        interface: OperationNameResultInterface
    }
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_interface_fragment_single_fragment(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

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
    type OperationNameResultInterfaceBlogPost = {
        id: string
        title: string
    }

    type OperationNameResult = {
        interface: OperationNameResultInterfaceBlogPost
    }
    """

    # TODO: do we need the verbosity here?

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


def test_interface_fragment(schema):
    generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

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
    type OperationNameResultInterfaceBlogPost = {
        id: string
        title: string
    }

    type OperationNameResultInterfaceImage = {
        id: string
        url: string
    }

    type OperationNameResultInterface = OperationNameResultInterfaceBlogPost | OperationNameResultInterfaceImage

    type OperationNameResult = {
        interface: OperationNameResultInterface
    }
    """

    result = generator.codegen(input_query)

    assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()
