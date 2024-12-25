import strawberry
from strawberry.extensions import DisableValidation, ParserCache


@strawberry.type
class Birthday:
    year: int


@strawberry.type
class User:
    id: strawberry.ID
    name: str
    birthday: Birthday

    @strawberry.field
    @staticmethod
    def articles(root) -> list["Article"]:
        return list(
            Article(id=strawberry.ID(str(i)), title=f"Article {i}", author=root)
            for i in range(10)
        )


@strawberry.type
class Article:
    id: strawberry.ID
    title: str
    author: User


@strawberry.type
class Query:
    @strawberry.field
    @staticmethod
    async def search(query: str, first: int = 10) -> list[Article]:
        return list(
            Article(
                id=strawberry.ID(str(i)),
                title=f"Article {i}",
                author=User(
                    id=strawberry.ID(str(i)),
                    name=f"User {i}",
                    birthday=Birthday(year=2000),
                ),
            )
            for i in range(first)
        )


schema = strawberry.Schema(query=Query, extensions=[DisableValidation(), ParserCache()])
