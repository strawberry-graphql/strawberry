from typing import List

class addBlogPostsResultAddBlogPostsPosts:
    title: str

class addBlogPostsResultAddBlogPosts:
    posts: List[addBlogPostsResultAddBlogPostsPosts]

class addBlogPostsResult:
    add_blog_posts: addBlogPostsResultAddBlogPosts

class BlogPostInput:
    title: str

class addBlogPostsVariables:
    input: List[BlogPostInput]
