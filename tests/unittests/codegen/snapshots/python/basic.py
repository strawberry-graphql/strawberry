from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID


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
