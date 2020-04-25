from graphql import GraphQLSchema
from graphql.type.directives import specified_directives
from graphql.utilities.print_schema import print_schema


# TODO: typings


class Schema(GraphQLSchema):
    def __init__(
        self, query, mutation=None, subscription=None, directives=(), types=()
    ):
        """
        Wrapper around the GraphQLSchema, but compatible
        with Strawberry types and directives.

        :param query: the root query to use for the schema
        :param mutation: the basic mutation type (if any)
        :param subscription: the subscription type (if any)
        :param directives: (additional) Strawberry directives
        :param types: additional Strawberry types to register, return values of fields
                      are automatically registered while return types for interfaces have
                      to be manually registered
        """
        super().__init__(
            query=query.graphql_type,
            mutation=mutation.graphql_type if mutation else None,
            subscription=subscription.graphql_type if subscription else None,
            directives=specified_directives
            + [directive.directive for directive in directives],
            types=[type.graphql_type for type in types],
        )

    def __repr__(self):
        return print_schema(self)
