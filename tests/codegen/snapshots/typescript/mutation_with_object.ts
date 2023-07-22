type AddBlogPostsResultAddBlogPostsPosts = {
    title: string
}

type AddBlogPostsResultAddBlogPosts = {
    posts: AddBlogPostsResultAddBlogPostsPosts[]
}

type AddBlogPostsResult = {
    add_blog_posts: AddBlogPostsResultAddBlogPosts
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
    a_bool: boolean
    an_int: number
    an_optional_int: number | undefined
}

type AddBlogPostsVariables = {
    input: BlogPostInput[]
}
