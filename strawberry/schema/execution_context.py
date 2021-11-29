from typing import List

from graphql import ExecutionContext
from graphql.language import FieldNode
from graphql.pyutils import Path
from graphql.type import GraphQLField, GraphQLObjectType

from strawberry.types.info import Info


class StrawberryExecutionContext(ExecutionContext):
    def build_resolve_info(
        self,
        field_def: GraphQLField,
        field_nodes: List[FieldNode],
        parent_type: GraphQLObjectType,
        path: Path,
    ) -> Info:  # type: ignore
        raw_info = super().build_resolve_info(
            field_def,
            field_nodes,
            parent_type,
            path,
        )

        return Info(
            _raw_info=raw_info,
            # TODO: ...
            _field=None,
        )
