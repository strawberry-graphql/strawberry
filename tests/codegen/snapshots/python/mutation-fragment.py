from typing_extensions import TypedDict

class IdFragment(TypedDict):
    # typename: BlogPost
    id: str

class addBookResult(TypedDict):
    add_book: IdFragment

class addBookVariables(TypedDict):
    input: str
