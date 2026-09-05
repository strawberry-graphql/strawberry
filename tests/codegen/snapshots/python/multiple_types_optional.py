from typing_extensions import TypedDict
from typing import Optional

class OperationNameResultOptionalPerson(TypedDict):
    name: str

class OperationNameResult(TypedDict):
    optional_person: Optional[OperationNameResultOptionalPerson]
