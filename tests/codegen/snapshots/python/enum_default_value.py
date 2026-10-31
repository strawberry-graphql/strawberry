from enum import Enum

class SortOrder(Enum):
    ASC = "ASC"
    DESC = "DESC"

class OperationNameResult:
    order: SortOrder

class SearchInput:
    order: SortOrder = SortOrder.DESC

class OperationNameVariables:
    input: SearchInput
