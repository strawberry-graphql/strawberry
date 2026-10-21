from typing_extensions import TypedDict

class UserFields(TypedDict):
    # typename: User
    id: str
    name: str

class RelayFragmentResult(TypedDict):
    node: UserFields
