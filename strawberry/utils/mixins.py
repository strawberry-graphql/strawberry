from typing import Optional

from strawberry.utils.str_converters import to_camel_case


class GraphQLNameMixin:
    python_name: str
    graphql_name: Optional[str]

    def get_graphql_name(self, auto_camel_case: bool) -> str:
        if self.graphql_name is not None:
            return self.graphql_name

        assert self.python_name

        if auto_camel_case:
            return to_camel_case(self.python_name)

        return self.python_name
