import typing

from graphql import GraphQLSchema
from graphql.type.directives import specified_directives
from graphql.utilities.print_schema import print_schema

from .extensions import Extension


class Schema(GraphQLSchema):
    strawberry_extensions: typing.Sequence[Extension]

    def __init__(
        self,
        query: typing.Type,
        mutation: typing.Type = None,
        subscription: typing.Type = None,
        directives: typing.Sequence[typing.Type] = (),
        types: typing.Sequence[typing.Type] = (),
        extensions: typing.Sequence[Extension] = (),
    ):
        super().__init__(
            query=query.graphql_type,
            mutation=mutation.graphql_type if mutation else None,
            subscription=subscription.graphql_type if subscription else None,
            directives=(
                specified_directives + [directive.directive for directive in directives]
            ),
            types=[type.graphql_type for type in types],
        )

        self.strawberry_extensions = extensions

    def __repr__(self):
        return print_schema(self)
