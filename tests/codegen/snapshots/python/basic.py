from typing_extensions import TypedDict
from uuid import UUID
from datetime import date, datetime, time
from decimal import Decimal

class OperationNameResultLazy(TypedDict):
    something: bool

class OperationNameResult(TypedDict):
    id: str
    integer: int
    float: float
    boolean: bool
    uuid: UUID
    date: date
    datetime: datetime
    time: time
    decimal: Decimal
    lazy: OperationNameResultLazy
