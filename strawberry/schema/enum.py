from enum import Enum
from typing import Any, Dict, Optional

from graphql import GraphQLEnumType


# graphql-core expects a resolver for an Enum type to return
# the enum's *value* (not its name or an instance of the enum). We have to
# subclass the GraphQLEnumType class to enable returning Enum members from
# resolvers.


class CustomGraphQLEnumType(GraphQLEnumType):
    def __init__(
        self,
        name: str,
        values: Dict[str, Any],
        description: Optional[str],
        enum_values_from: str,
    ) -> None:
        super().__init__(name, values, description)

        self.enum_values_from = enum_values_from

    def serialize(self, output_value: Any) -> str:
        if isinstance(output_value, Enum):
            return output_value.name

        return "LOL"

        return super().serialize(output_value)
