from graphql.validation import NoSchemaIntrospectionCustomRule

from strawberry.extensions import AddValidationRules


class DisableIntrospection(AddValidationRules):
    """Disable introspection queries.

    Example:

    ```python
    import strawberry
    from strawberry.extensions import DisableIntrospection


    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "Hello, world!"


    schema = strawberry.Schema(
        Query,
        extensions=[
            DisableIntrospection(),
        ],
    )
    ```
    """

    def __init__(self) -> None:
        super().__init__([NoSchemaIntrospectionCustomRule])


__all__ = ["DisableIntrospection"]
