type AddBlogPostsResultAddBlogPostsPosts = {
    title: string
}

type AddBlogPostsResultAddBlogPosts = {
    posts: AddBlogPostsResultAddBlogPostsPosts
}

type AddBlogPostsResult = {
    addBlogPosts: AddBlogPostsResultAddBlogPosts
}

enum Color {
    RED = "RED",
    GREEN = "GREEN",
    BLUE = "BLUE",
}

type BlogPostInput = {
    title: string
    color: Color
    pi: number
    aBool: boolean
    anInt: number
    anOptionalInt: number
}

type AddBlogPostsVariables = {
    input: BlogPostInput[]
}
