from typing import List

class OperationNameResult:
    optional_int: int | None
    list_of_int: list[int]
    list_of_optional_int: list[int | None]
    optional_list_of_optional_int: list[int | None] | None
