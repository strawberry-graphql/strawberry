type UpdateBlogPostResult = {
    update_blog_post: boolean
}

type UpdateBlogPostInput = {
    title: string | undefined
    subtitle: string | undefined
    tags: string[] | undefined
}

type UpdateBlogPostVariables = {
    input: UpdateBlogPostInput
}
