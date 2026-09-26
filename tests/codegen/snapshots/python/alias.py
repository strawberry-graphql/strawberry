from typing_extensions import TypedDict

class OperationNameResultLazy(TypedDict):
    # alias for something
    lazy: bool

class OperationNameResult(TypedDict):
    id: str
    # alias for id
    second_id: str
    # alias for float
    a_float: float
    lazy: OperationNameResultLazy
