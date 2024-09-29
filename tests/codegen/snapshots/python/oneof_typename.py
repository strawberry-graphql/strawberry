from typing import Union

class OneOfTypenameTestResultOneOfTypenamePerson:
    # typename: Person
    name: str
    age: int

class OneOfTypenameTestResult:
    # alias for one_of_typename
    alias: OneOfTypenameTestResultOneOfTypenamePerson

class OneOfInputA:
    a: str

class OneOfInputB:
    b: str

OneOfInput = Union[OneOfInputA,OneOfInputB]

class OneOfTypenameTestVariables:
    value: OneOfInput
