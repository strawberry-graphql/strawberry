import strawberry
from strawberry.types.info import Info


def function_resolver(root) -> str:
    return "I'm a function resolver"


@strawberry.type
class Query:
    @strawberry.field
    def user(self, info: Info) -> str:
        return "🍓"

    hello: str = "🍓"
    hello_field: str = strawberry.field(resolver=function_resolver)


schema = strawberry.Schema(query=Query)
