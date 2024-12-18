from typing import List, Optional
from enum import Enum

class AddBlogPostsResultAddBlogPostsPosts:
    title: str

class AddBlogPostsResultAddBlogPosts:
    posts: list[AddBlogPostsResultAddBlogPostsPosts]

class AddBlogPostsResult:
    add_blog_posts: AddBlogPostsResultAddBlogPosts

class Color(Enum):
    RED = "RED"
    GREEN = "GREEN"
    BLUE = "BLUE"

class BlogPostInput:
    title: str = "I replaced my doorbell.  You wouldn't believe what happened next!"
    color: Color = Color.RED
    pi: float = 3.14159
    a_bool: bool = True
    an_int: int = 42
    an_optional_int: Optional[int] = None

class AddBlogPostsVariables:
    input: list[BlogPostInput]
