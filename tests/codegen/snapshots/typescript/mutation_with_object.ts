type addBlogPostsResultAddBlogPostsPosts = {
    title: string
}

type addBlogPostsResultAddBlogPosts = {
    posts: addBlogPostsResultAddBlogPostsPosts[]
}

type addBlogPostsResult = {
    add_blog_posts: addBlogPostsResultAddBlogPosts
}

type addBlogPostsVariables = {
    input: BlogPostInput[]
}

type BlogPostInput = {
    title: string
}
