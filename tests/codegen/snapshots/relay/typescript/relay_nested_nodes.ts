type RelayNestedNodesResultPostAuthor = {
    id: string
    name: string
}

type RelayNestedNodesResultPost = {
    id: string
    title: string
    author: RelayNestedNodesResultPostAuthor
}

type RelayNestedNodesResult = {
    post: RelayNestedNodesResultPost
}
