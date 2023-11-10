from enum import Enum
from typing import List

class AddBlogPostsResultAddBlogPostsPosts:
    title: str

class AddBlogPostsResultAddBlogPosts:
    posts: AddBlogPostsResultAddBlogPostsPosts

class AddBlogPostsResult:
    addBlogPosts: AddBlogPostsResultAddBlogPosts

class Color(Enum):
    RED = "RED"
    GREEN = "GREEN"
    BLUE = "BLUE"

class BlogPostInput:
    title: str
    color: Color
    pi: float
    aBool: bool
    anInt: int
    anOptionalInt: int

class AddBlogPostsVariables:
    input: List[BlogPostInput]
