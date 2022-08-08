import dataclasses
from typing import List, Set

from graphql.type.directives import GraphQLDirective


@dataclasses.dataclass
class PrintExtras:
    directives: List[GraphQLDirective] = dataclasses.field(default_factory=list)
    types: Set[type] = dataclasses.field(default_factory=set)
