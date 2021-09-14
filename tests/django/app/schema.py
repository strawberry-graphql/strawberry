import strawberry
from strawberry.types.info import Info


@strawberry.type
class Query:
    @strawberry.field
    def user(self, info: Info) -> str:
        return "🍓"


schema = strawberry.Schema(query=Query)
