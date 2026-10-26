from enum import Enum

class Clause(Enum):
    from_ = "from"
    WHERE = "WHERE"

class OperationNameResult:
    from_: str
    # alias for id
    import_: str
    clause: Clause
    with_keyword_input: bool

class KeywordInput:
    class_: str

class OperationNameVariables:
    class_: KeywordInput
