import strawberry


def hello_resolver(root) -> str:
    return "🍓"


@strawberry.type
class Query:
    hello: str = strawberry.field(resolver=hello_resolver)


schema = strawberry.Schema(query=Query)
