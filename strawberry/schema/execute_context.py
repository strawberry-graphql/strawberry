from typing import Any, Dict, List, Optional, Union

from promise import Promise, is_thenable, promise_for_dict

from graphql import (
    ExecutionContext,
    GraphQLError,
    GraphQLField,
    GraphQLFieldResolver,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLResolveInfo,
)
from graphql.execution.values import get_argument_values
from graphql.language import FieldNode
from graphql.pyutils import AwaitableOrValue, Path, Undefined


class ExecutionContextWithPromise(ExecutionContext):
    def build_response(self, data):
        if is_thenable(data):
            original_build_response = super().build_response

            def on_rejected(error):
                self.errors.append(error)
                return None

            def on_resolve(data):
                return original_build_response(data)

            promise = data.catch(on_rejected).then(on_resolve)
            return promise
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
        results = {}
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
