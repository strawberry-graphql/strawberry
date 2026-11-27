class RelayNestedNodesResultPostAuthor:
    id: str
    'The Globally Unique ID of this object'
    name: str

class RelayNestedNodesResultPost:
    id: str
    'The Globally Unique ID of this object'
    title: str
    author: RelayNestedNodesResultPostAuthor

class RelayNestedNodesResult:
    post: RelayNestedNodesResultPost
