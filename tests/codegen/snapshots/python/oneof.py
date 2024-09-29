from typing import Union

class OneOfTestResult:
    one_of: str

class OneOfInputA:
    a: str

class OneOfInputB:
    b: str

OneOfInput = Union[OneOfInputA,OneOfInputB]

class OneOfTestVariables:
    value: OneOfInput
