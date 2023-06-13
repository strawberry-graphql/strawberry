type AddBlogPostsResultAddBlogPostsPosts = {
    title: string
}

type AddBlogPostsResultAddBlogPosts = {
    posts: AddBlogPostsResultAddBlogPostsPosts[]
}

type AddBlogPostsResult = {
    add_blog_posts: AddBlogPostsResultAddBlogPosts
}

type BlogPostInput = {
    title: string
}

type AddBlogPostsVariables = {
    input: BlogPostInput[]
}
