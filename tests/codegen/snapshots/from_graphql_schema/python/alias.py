class OperationNameResultLazy:
    # alias for something
    lazy: bool

class OperationNameResult:
    id: str
    # alias for id
    second_id: str
    # alias for float
    a_float: float
    lazy: OperationNameResultLazy
