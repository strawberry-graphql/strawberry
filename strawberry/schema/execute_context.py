from typing import Any, Dict, Hashable, List, Optional, TypeVar, Union

from promise import Promise, is_thenable

from graphql import (
    ExecutionContext,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLResolveInfo,
)
from graphql.language import FieldNode, OperationDefinitionNode
from graphql.pyutils import (
    AwaitableOrValue,
    Path,
    Undefined,
    is_awaitable as default_is_awaitable,
)


def is_awaitable(value):
    """
    Create custom is_awaitable function to make sure that Promises' aren't
    considered awaitable
    """
    if is_thenable(value):
        return False
    return default_is_awaitable(value)


S = TypeVar("S")


def promise_for_dict(
    value: Dict[Hashable, Union[S, Promise[S]]]
) -> Promise[Dict[Hashable, S]]:
    """
    A special function that takes a dictionary of promises
    and turns them into a promise for a dictionary of values.
    """

    def handle_success(resolved_values: List[S]) -> Dict[Hashable, S]:
        return_value = zip(value.keys(), resolved_values)
        return dict(return_value)

    return Promise.all(value.values()).then(handle_success)


class ExecutionContextWithPromise(ExecutionContext):
    is_awaitable = staticmethod(is_awaitable)

    def execute_operation(
        self, operation: OperationDefinitionNode, root_value: Any
    ) -> Optional[AwaitableOrValue[Any]]:
        # Wrap execute in a Promise
        original_execute_operation = super().execute_operation

        def promise_executor(v):
            return original_execute_operation(operation, root_value)

        promise = Promise.resolve(None).then(promise_executor)
        return promise

    def build_response(self, data):
        if is_thenable(data):
            original_build_response = super().build_response

            def on_rejected(error):
                self.errors.append(error)
                return None

            def on_resolve(data):
                return original_build_response(data)

            promise = data.catch(on_rejected).then(on_resolve)
            return promise.get()
        return super().build_response(data)

    def complete_value_catching_error(
        self,
        return_type: GraphQLOutputType,
        field_nodes: List[FieldNode],
        info: GraphQLResolveInfo,
        path: Path,
        result: Any,
    ) -> AwaitableOrValue[Any]:
        """Complete a value while catching an error.
        This is a small wrapper around completeValue which detects and logs errors in
        the execution context.
        """
        completed: AwaitableOrValue[Any]
        try:
            if is_thenable(result):

                def handle_error(error):
                    self.handle_field_error(error, field_nodes, path, return_type)

                completed = Promise.resolve(result).then(
                    lambda resolved: self.complete_value(
                        return_type, field_nodes, info, path, resolved
                    ),
                    handle_error,
                )
            else:
                completed = self.complete_value(
                    return_type, field_nodes, info, path, result
                )
            return completed
        except Exception as error:
            self.handle_field_error(error, field_nodes, path, return_type)
            return None

    def execute_fields(
        self,
        parent_type: GraphQLObjectType,
        source_value: Any,
        path: Optional[Path],
        fields: Dict[str, List[FieldNode]],
    ):
        """Execute the given fields concurrently.

        Implements the "Evaluating selection sets" section of the spec for "read" mode.
        """
        contains_promise = False
        results: Dict[Hashable, Union[Promise[Any], Any]] = {}
        for response_name, field_nodes in fields.items():
            field_path = Path(path, response_name)
            result = self.resolve_field(
                parent_type, source_value, field_nodes, field_path
            )
            if result is not Undefined:
                results[response_name] = result
                if is_thenable(result):
                    contains_promise = True

        if contains_promise:
            return promise_for_dict(results)

        return results
