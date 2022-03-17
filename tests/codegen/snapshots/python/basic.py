from uuid import UUID
from datetime import date, datetime, time
from decimal import Decimal

class OperationNameResultLazy:
    something: bool

class OperationNameResult:
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
