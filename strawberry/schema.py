from graphql import GraphQLSchema
from graphql.type.directives import specified_directives
from graphql.utilities.schema_printer import print_schema


# TODO: typings


class Schema(GraphQLSchema):
    def __init__(self, query, mutation=None, subscription=None, directives=()):
        super().__init__(
            query=query.field,
            mutation=mutation.field if mutation else None,
            subscription=subscription.field if subscription else None,
            directives=specified_directives
            + [directive.directive for directive in directives],
        )

    def __repr__(self):
        return print_schema(self)
