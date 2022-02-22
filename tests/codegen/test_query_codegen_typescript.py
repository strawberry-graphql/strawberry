# def test_codegen_basic(schema):
#     generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

#     input_query = """
#     query OperationName {
#         id
#         integer
#         anotherInteger
#     }
#     """

#     expected_output = """
#     type OperationNameResult = {
#         id: string
#         integer: number
#         another_integer: number
#     }
#     """

#     result = generator.codegen(input_query)

#     assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


# def test_list_and_optional(schema):
#     generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

#     input_query = """
#     query OperationName {
#         optionalInt
#         listOfOptionalInt
#     }
#     """

#     expected_output = """
#     from typing import List, Optional

#     class OperationNameResult:
#         optional_int: Optional[int]
#         list_of_optional_int: List[Optional[int]]
#     """

#     result = generator.codegen(input_query)

#     assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


# def test_multiple_types(schema):
#     generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

#     input_query = """
#     query OperationName {
#         person {
#             name
#         }
#     }
#     """

#     expected_output = """
#     class OperationNameResultPerson:
#         name: str

#     class OperationNameResult:
#         person: OperationNameResultPerson
#     """

#     result = generator.codegen(input_query)

#     assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


# def test_multiple_types_optional(schema):
#     generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

#     input_query = """
#     query OperationName {
#         optionalPerson {
#             name
#         }
#     }
#     """

#     expected_output = """
#     from typing import Optional

#     class OperationNameResultOptionalPerson:
#         name: str

#     class OperationNameResult:
#         optional_person: Optional[OperationNameResultOptionalPerson]
#     """

#     result = generator.codegen(input_query)

#     assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


# def test_enum(schema):
#     generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

#     input_query = """
#     query OperationName {
#         enum
#     }
#     """

#     expected_output = """
#     from enum import Enum

#     class OperationNameResultEnum(Enum):
#         red = "red"
#         green = "green"
#         blue = "blue"

#     class OperationNameResult:
#         enum: OperationNameResultEnum
#     """

#     result = generator.codegen(input_query)

#     assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


# def test_scalar(schema):
#     generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

#     input_query = """
#     query OperationName {
#         json
#     }
#     """

#     expected_output = """
#     from typing import NewType

#     JSON = NewType("JSON", str)

#     class OperationNameResult:
#         json: JSON
#     """

#     result = generator.codegen(input_query)

#     assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


# def test_union(schema):
#     generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

#     input_query = """
#     query OperationName {
#         union {
#             ... on Animal {
#                 age
#             }
#             ... on Person {
#                 name
#             }
#         }
#     }
#     """

#     expected_output = """
#     from typing import Union

#     class OperationNameResultUnionAnimal:
#         age: int

#     class OperationNameResultUnionPerson:
#         name: str

#     class OperationNameResult:
#         union: Union[OperationNameResultUnionAnimal, OperationNameResultUnionPerson]
#     """

#     result = generator.codegen(input_query)

#     assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


# def test_interface(schema):
#     generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

#     input_query = """
#     query OperationName {
#         interface {
#             id
#         }
#     }
#     """

#     expected_output = """
#     class OperationNameResultInterface:
#         id: str

#     class OperationNameResult:
#         interface: OperationNameResultInterface
#     """

#     result = generator.codegen(input_query)

#     assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()


# def test_interface_fragment(schema):
#     generator = QueryCodegen(schema, plugins=[TypeScriptPlugin()])

#     input_query = """
#     query OperationName {
#         interface {
#             id

#             ... on BlogPost {
#                 title
#             }
#         }
#     }
#     """

#     expected_output = """
#     class OperationNameResultInterfaceBlogPost:
#         id: str
#         title: str

#     class OperationNameResult:
#         interface: OperationNameResultInterface
#     """

#     result = generator.codegen(input_query)

#     assert textwrap.dedent(result).strip() == textwrap.dedent(expected_output).strip()
