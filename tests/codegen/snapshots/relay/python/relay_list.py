class RelayListResultUsers:
    id: str
    'The Globally Unique ID of this object'
    name: str

class RelayListResult:
    users: list[RelayListResultUsers]
