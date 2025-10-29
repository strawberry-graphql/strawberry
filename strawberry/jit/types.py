"""Type definitions for JIT compiler."""

from __future__ import annotations

from graphql import GraphQLSchema


class MockInfo:
    """Mock GraphQLResolveInfo for JIT compilation.

    This class provides a minimal info object structure that matches
    the GraphQLResolveInfo interface used by resolvers.
    """

    def __init__(self, schema: GraphQLSchema):
        self.schema = schema
        self.field_name = None
        self.parent_type = None
        self.return_type = None
        self.path = []
        self.operation = None
        self.variable_values = {}
        self.context = None
        self.root_value = None
        self.fragments = {}


__all__ = ["MockInfo"]
