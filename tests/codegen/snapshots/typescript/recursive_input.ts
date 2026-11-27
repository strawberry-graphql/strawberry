type OperationNameResult = {
    filter_posts: boolean
}

type PostFilter = {
    title: string | undefined
    any_of: PostFilter[] | undefined
    author: AuthorFilter | undefined
}

type AuthorFilter = {
    name: string | undefined
    posts: PostFilter | undefined
}

type OperationNameVariables = {
    filter: PostFilter | undefined
}
