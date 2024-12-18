from __future__ import annotations

from enum import Enum
from typing import Annotated, Union

import strawberry


@strawberry.enum
class Role(Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"


@strawberry.interface
class Node:
    id: strawberry.ID


@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None


@strawberry.type
class User(Node):
    id: strawberry.ID
    username: str
    email: str
    role: Role

    @classmethod
    def random(cls, seed: int) -> User:
        return User(
            id=strawberry.ID(str(int)),
            username=f"username={seed}",
            email=f"email={seed}",
            role=Role.ADMIN,
        )

    @strawberry.field
    def posts(self, first: int = 10, after: str | None = None) -> PostConnection | None:
        return PostConnection(
            edges=[
                PostEdge(
                    node=Post.random(i),
                    cursor=str(i),
                )
                for i in range(first)
            ],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        )


@strawberry.type
class Post(Node):
    id: strawberry.ID
    title: str
    content: str
    author: User

    @classmethod
    def random(cls, seed: int) -> Post:
        return Post(
            id=strawberry.ID(str(int)),
            title=f"title={seed}",
            content=f"content={seed}",
            author=User.random(seed),
        )

    @strawberry.field
    def comments(
        self, first: int = 10, after: str | None = None
    ) -> CommentConnection | None:
        return CommentConnection(
            edges=[
                CommentEdge(
                    node=Comment.random(i),
                    cursor=str(i),
                )
                for i in range(first)
            ],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        )


@strawberry.type
class Comment(Node):
    id: strawberry.ID
    text: str
    author: User
    post: Post

    @classmethod
    def random(cls, seed: int) -> Comment:
        return Comment(
            id=strawberry.ID(str(int)),
            text=f"text={seed}",
            author=User.random(seed),
            post=Post.random(seed),
        )


@strawberry.type
class UserConnection:
    edges: list[UserEdge | None] | None
    page_info: PageInfo


@strawberry.type
class UserEdge:
    node: User | None
    cursor: str


@strawberry.type
class PostConnection:
    edges: list[PostEdge | None] | None
    page_info: PageInfo


@strawberry.type
class PostEdge:
    node: Post | None
    cursor: str


@strawberry.type
class CommentConnection:
    edges: list[CommentEdge | None] | None
    page_info: PageInfo


@strawberry.type
class CommentEdge:
    node: Comment | None
    cursor: str


SearchResult = Annotated[
    Union[User, Post, Comment], strawberry.union(name="SearchResult")
]


@strawberry.type
class Query:
    users: UserConnection | None
    posts: PostConnection | None
    comments: CommentConnection | None

    @strawberry.field
    async def search(
        self, query: str, first: int = 10, after: str | None = None
    ) -> list[SearchResult | None] | None:
        div = 3

        chunks = [first // div + (1 if x < first % div else 0) for x in range(div)]

        return [
            *[User.random(i) for i in range(chunks[0])],
            *[Post.random(i) for i in range(chunks[1])],
            *[Comment.random(i) for i in range(chunks[2])],
        ]


schema = strawberry.Schema(query=Query)
