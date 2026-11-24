from typing import Optional

class UpdateBlogPostResult:
    update_blog_post: bool

class UpdateBlogPostInput:
    title: Optional[str] = None
    subtitle: Optional[str] = None
    tags: Optional[list[str]] = None

class UpdateBlogPostVariables:
    input: UpdateBlogPostInput
