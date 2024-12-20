from __future__ import annotations

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    Optional,
    Union,
)

from graphql.language import (
    FieldNode,
    FragmentDefinitionNode,
    Node,
    OperationDefinitionNode,
)
from graphql.language.ast import FragmentSpreadNode, VariableNode

from strawberry.extensions.base_extension import SchemaExtension
from strawberry.extensions.field_extension import FieldExtension
from strawberry.extensions.query_depth_limiter import (
    FieldArgumentsType,
    get_fragments,
    get_queries_and_mutations,
    resolve_field_value,
)
from strawberry.types.base import StrawberryContainer
from strawberry.utils.str_converters import to_snake_case

if TYPE_CHECKING:
    from strawberry.types import ExecutionContext
    from strawberry.types.field import StrawberryField
    from strawberry.types.info import Info


@dataclass(frozen=True)
class NonRootTypeInfo:
    """Useful info about a type which is not the root type."""

    parent_type_name: str
    name: str

    source_field: StrawberryField
    estimator: Optional[FieldComplexityEstimator] = None


@dataclass(frozen=True)
class RootTypeInfo:
    """Constant type info about the `Query` type."""

    name: str
    VALUE: ClassVar[RootTypeInfo]


RootTypeInfo.VALUE = RootTypeInfo(name="Query")

TypeInfo = Union[RootTypeInfo, NonRootTypeInfo]


class FieldComplexityEstimator(FieldExtension):
    """Estimate the complexity of a GraphQL field."""

    def estimate_complexity(
        self, child_complexities: Iterator[int], arguments: FieldArgumentsType
    ) -> int:
        """Estimate the complexity of a field.

        Args:
            child_complexities: An iterator over the complexities of child fields,
                if they exist. This iterator is lazy, meaning the complexity of each
                child will only be evaluated if `next()` gets called on the iterator.
                As such, to avoud unnnecessary computation we recommend only iterating
                over child complexities if you'll use them.
            arguments: A dict that maps field arguments to their values.
        """
        return 1

    def resolve(
        self, next_: Callable[..., Any], source: Any, info: Info, **kwargs: Any
    ) -> Any:
        return next_(source, info, **kwargs)


class SimpleFieldComplexityEstimator(FieldComplexityEstimator):
    """Simple complexity estimator.

    If attached to scalar fields, will return `scalar_complexity`.
    If attached to object fields, will return the sum of the complexities
    of the object's fields.
    """

    def __init__(self, scalar_complexity: int = 1) -> None:
        self.scalar_complexity = scalar_complexity

    def estimate_complexity(
        self, child_complexities: Iterator[int], arguments: FieldArgumentsType
    ) -> int:
        first_complexity = next(child_complexities, None)
        if first_complexity is None:
            return self.scalar_complexity

        return first_complexity + sum(child_complexities)


class ConstantFieldComplexityEstimator(FieldComplexityEstimator):
    """Estimate field complexity as a constant, ignoring child fields."""

    def __init__(self, complexity: int = 1) -> None:
        self.complexity = complexity

    def estimate_complexity(
        self, child_complexities: Iterator[int], arguments: FieldArgumentsType
    ) -> int:
        return self.complexity


class QueryComplexityEstimator(SchemaExtension):
    """Estimate the complexity of a query and attach its cost to the execution context.

    This extension works by traversing through the query document and evaluating each
    node's cost. If no field-specific override is provided, field costs are estimated
    using `default_estimator`.

    When the extension finishes estimating the complexity of the operations, `callback`
    is called with a map of complexities of all operations and the current execution
    context. This callback can be used for things such as a token-bucket rate-limiter
    based on query complexity, a complexity logger, or for simply storing the complexities
    in the current execution context so that it can used by downstream resolvers.

    Additionally, you can configure the extension also to add the complexity dictionary to
    the response that gets sent to the client by setting `response_key`.

    Example:

    ```python
    from typing import Iterator

    from graphql.error import GraphQLError

    import strawberry
    from strawberry.types import ExecutionContext
    from strawberry.extensions import FieldComplexityEstimator, QueryComplexityEstimator


    class MyEstimator(FieldComplexityEstimator):
        def estimate_complexity(
            self, child_complexities: Iterator[int], arguments: dict[str, Any]
        ) -> int:
            children_sum = sum(child_complexities)
            # scalar fields cost 1
            if children_sum == 0:
                return 1

            # non-list object fields cost the sum of their children
            if "page_size" not in arguments:
                return children_sum

            # paginated fields cost gets multiplied by page size
            return children_sum * arguments["page_size"]


    # initialize your rate-limiter somehow
    rate_limiter = ...


    def my_callback(
        complexities: dict[str, int], execution_context: ExecutionContext
    ) -> None:
        # add complexities to execution context
        execution_context.context["complexities"] = complexities

        # apply a token-bucket rate-limiter
        total_cost = sum(complexities.values())
        bucket = rate_limiter.get_bucket_for_key(execution_context.context["user_id"])
        tokens_left = bucket.take_tokens(total_cost)
        if tokens_left <= 0:
            raise GraphQLError(
                "Rate-limit exhausted. Please wait for some time before trying again."
            )


    schema = strawberry.Schema(
        Query,
        extensions=[
            QueryComplexityEstimator(
                default_estimator=MyEstimator(),
                callback=my_callback,
            ),
        ],
    )
    ```
    """

    def __init__(
        self,
        default_estimator: Union[FieldComplexityEstimator, int],
        callback: Optional[Callable[[Dict[str, int], ExecutionContext], None]] = None,
        response_key: Optional[str] = None,
    ) -> None:
        """Initialize the QueryComplexityEstimator.

        Args:
            default_estimator: The default complexity estimator for fields
                that don't specify overrides. If it's an integer, the default
                estimator will be a `ConstantFieldComplexityEstimator` with
                the integer value.
            callback: Called each time complexity is estimated. Receives a
                dictionary which is a map of estimated complexity for each
                operation.
            response_key: If provided, this extension will add the calculated
                query complexities to the response that gets sent to the
                client via `get_results()`. The resulting complexities will
                be under the specified key.
        """
        if isinstance(default_estimator, int):
            default_estimator = ConstantFieldComplexityEstimator(
                complexity=default_estimator
            )

        self.estimator: FieldComplexityEstimator = default_estimator
        self.callback = callback

        self.response_key = response_key
        self.results: Dict[str, int] = {}

        super().__init__()

    def get_results(self) -> Dict[str, Any]:
        if self.response_key is None:
            return {}

        key = self.execution_context.schema.config.name_converter.apply_naming_config(
            self.response_key
        )

        return {key: self.results}

    def on_validate(self) -> Iterator[None]:
        doc = self.execution_context.graphql_document
        assert doc is not None
        schema = self.execution_context.schema
        assert schema.query is not None

        fragments = get_fragments(doc.definitions)
        queries = get_queries_and_mutations(doc.definitions)
        query_complexities: Dict[str, int] = {
            name: self._estimate_cost(
                parent_type=RootTypeInfo.VALUE,
                node=query,
                fragments=fragments,
            )
            for name, query in queries.items()
        }

        self.results = query_complexities

        if callable(self.callback):
            self.callback(query_complexities, self.execution_context)

        yield

    def _get_type_info(self, parent_type_name: str, field_name: str) -> TypeInfo:
        schema = self.execution_context.schema
        strawberry_field = schema.get_field_for_type(field_name, parent_type_name)
        assert strawberry_field is not None

        field_type = strawberry_field.type_annotation.resolve()
        if isinstance(field_type, StrawberryContainer):
            field_type_name = field_type.of_type.__name__
        else:
            field_type_name = field_type.__name__

        field_estimators = [
            e
            for e in strawberry_field.extensions
            if isinstance(e, FieldComplexityEstimator)
        ]
        field_estimator = field_estimators[0] if len(field_estimators) > 0 else None

        return NonRootTypeInfo(
            parent_type_name=parent_type_name,
            name=field_type_name,
            source_field=strawberry_field,
            estimator=field_estimator,
        )

    def _child_complexities_lazy(
        self,
        node: Union[FieldNode, FragmentDefinitionNode],
        node_type: TypeInfo,
        fragments: Dict[str, FragmentDefinitionNode],
    ) -> Iterator[int]:
        """A lazy generator over the complexities of the children of a node.

        Instead of eagerly evaluating child complexities, we pass a lazy generator to the
        evaluator. The advantage with this is that the evaluator can decide to just
        ignore child costs, and then we don't waste time calculating them
        """
        if node.selection_set is None:
            return

        for child in node.selection_set.selections:
            yield self._estimate_cost(
                parent_type=node_type,
                node=child,
                fragments=fragments,
            )

    def _estimate_cost(
        self,
        parent_type: TypeInfo,
        node: Node,
        fragments: Dict[str, FragmentDefinitionNode],
    ) -> int:
        if isinstance(node, OperationDefinitionNode):
            return sum(
                self._estimate_cost(
                    parent_type=parent_type, node=child, fragments=fragments
                )
                for child in node.selection_set.selections
            )

        if isinstance(node, FieldNode):
            node_type = self._get_type_info(parent_type.name, node.name.value)
            variables = self.execution_context.variables or {}
            node_body = node
            args = {
                to_snake_case(arg.name.value): variables.get(arg.value.name.value, None)
                if isinstance(arg.value, VariableNode)
                else resolve_field_value(arg.value)
                for arg in node.arguments
            }
        elif isinstance(node, FragmentSpreadNode):
            if isinstance(parent_type, NonRootTypeInfo):
                assert parent_type.source_field.python_name is not None
                node_type = self._get_type_info(
                    parent_type.parent_type_name, parent_type.source_field.python_name
                )
            else:
                node_type = RootTypeInfo.VALUE

            node_body = fragments[node.name.value]
            args = {}
        else:
            raise TypeError(
                f"QueryComplexityEstimator cannot handle: {node.kind}"
            )  # pragma: no cover

        child_complexities = self._child_complexities_lazy(
            node_body, node_type, fragments
        )

        estimator = (
            node_type.estimator
            if isinstance(node_type, NonRootTypeInfo)
            and node_type.estimator is not None
            else parent_type.estimator
            if isinstance(parent_type, NonRootTypeInfo)
            and parent_type.estimator is not None
            else self.estimator
        )

        return estimator.estimate_complexity(child_complexities, args)


__all__ = [
    "ConstantFieldComplexityEstimator",
    "FieldComplexityEstimator",
    "QueryComplexityEstimator",
    "SimpleFieldComplexityEstimator",
]
