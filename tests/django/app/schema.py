import strawberry


@strawberry.type
class Query:
    hello: str = "🍓"


schema = strawberry.Schema(query=Query)
