from graphql.error.graphql_error import GraphQLError


class InvalidNullReturnError(GraphQLError):
    def __init__(self) -> None:
        super().__init__(
            message="Expected non-null return type for semanticNonNull field, but got null",
        )
