class RelayNestedNodesResultPostAuthor:
    id: str
    name: str

class RelayNestedNodesResultPost:
    id: str
    title: str
    author: RelayNestedNodesResultPostAuthor

class RelayNestedNodesResult:
    post: RelayNestedNodesResultPost
