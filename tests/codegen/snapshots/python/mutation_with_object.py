from typing_extensions import NotRequired, TypedDict
from typing import List, Optional
from enum import Enum

class AddBlogPostsResultAddBlogPostsPosts(TypedDict):
    title: str

class AddBlogPostsResultAddBlogPosts(TypedDict):
    posts: list[AddBlogPostsResultAddBlogPostsPosts]

class AddBlogPostsResult(TypedDict):
    add_blog_posts: AddBlogPostsResultAddBlogPosts

class Color(Enum):
    RED = "RED"
    GREEN = "GREEN"
    BLUE = "BLUE"

class BlogPostInput(TypedDict):
    title: NotRequired[str]
    color: NotRequired[Color]
    pi: NotRequired[float]
    a_bool: NotRequired[bool]
    an_int: NotRequired[int]
    an_optional_int: NotRequired[Optional[int]]

class AddBlogPostsVariables(TypedDict):
    input: list[BlogPostInput]
