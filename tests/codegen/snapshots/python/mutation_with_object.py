from typing import List

class AddBlogPostsResultAddBlogPostsPosts:
    title: str

class AddBlogPostsResultAddBlogPosts:
    posts: List[AddBlogPostsResultAddBlogPostsPosts]

class AddBlogPostsResult:
    add_blog_posts: AddBlogPostsResultAddBlogPosts

class BlogPostInput:
    title: str

class AddBlogPostsVariables:
    input: List[BlogPostInput]
