from graphql import GraphQLSchema


# TODO: typings


class Schema(GraphQLSchema):
    def __init__(self, query):
        super().__init__(query=self._build_query(query))

    def _build_query(self, query):
        return query.field
