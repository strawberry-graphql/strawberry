from graphql import GraphQLSchema


# TODO: typings


class Schema(GraphQLSchema):
    def __init__(self, query, mutation=None, subscription=None):
        super().__init__(
            query=query.field,
            mutation=mutation.field if mutation else None,
            subscription=subscription.field if subscription else None,
        )
