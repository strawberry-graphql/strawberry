import strawberry


@strawberry.type
class Query:
    camel_case: str = strawberry.field(
        name='camelCase',
    )
