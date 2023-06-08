type addBlogPostsResultAddBlogPostsPosts = {
    title: string
}

type addBlogPostsResultAddBlogPosts = {
    posts: addBlogPostsResultAddBlogPostsPosts[]
}

type addBlogPostsResult = {
    add_blog_posts: addBlogPostsResultAddBlogPosts
}

type BlogPostInput = {
    title: string
}

type addBlogPostsVariables = {
    input: BlogPostInput[]
}
