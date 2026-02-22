from typing_extensions import TypedDict

class GetNodeWithIDResultNodeUser(TypedDict):
    # typename: User
    id: str
    name: str

class GetNodeWithIDResult(TypedDict):
    node: GetNodeWithIDResultNodeUser
