from typing_extensions import TypedDict
from typing import List

class RelayListResultUsers(TypedDict):
    id: str
    name: str

class RelayListResult(TypedDict):
    users: list[RelayListResultUsers]
