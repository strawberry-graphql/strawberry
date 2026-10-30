from typing import Optional

class OperationNameResult:
    filter_posts: bool

class PostFilter:
    title: Optional[str] = None
    any_of: Optional[list["PostFilter"]] = None
    author: Optional["AuthorFilter"] = None

class AuthorFilter:
    name: Optional[str] = None
    posts: Optional[PostFilter] = None

class OperationNameVariables:
    filter: Optional[PostFilter]
