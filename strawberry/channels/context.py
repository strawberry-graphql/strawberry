from dataclasses import dataclass
from typing import TYPE_CHECKING, Union, cast


if TYPE_CHECKING:
    from strawberry.channels import GraphQLHTTPConsumer, GraphQLWSConsumer


@dataclass
class StrawberryChannelsContext:
    """
    A Channels context for GraphQL
    """

    request: Union["GraphQLHTTPConsumer", "GraphQLWSConsumer"]
    response: None = None

    @property
    def ws(self):
        return cast("GraphQLWSConsumer", self.request)

    def __getitem__(self, key):
        # __getitem__ override needed to avoid issues for who's
        # using info.context["request"]
        return super().__getattribute__(key)

    def get(self, key):
        """Enable .get notation for accessing the request"""
        return super().__getattribute__(key)
