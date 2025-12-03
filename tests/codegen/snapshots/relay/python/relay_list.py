from typing import List

class RelayListResultUsers:
    id: str
    name: str

class RelayListResult:
    users: list[RelayListResultUsers]
