from typing_extensions import TypedDict

class RelayNestedNodesResultPostAuthor(TypedDict):
    id: str
    name: str

class RelayNestedNodesResultPost(TypedDict):
    id: str
    title: str
    author: RelayNestedNodesResultPostAuthor

class RelayNestedNodesResult(TypedDict):
    post: RelayNestedNodesResultPost
