from typing import Any, Dict

from strawberry.types import ExecutionContext, Info


class Extension:
    def __init__(self, *, execution_context: ExecutionContext):
        self.execution_context = execution_context

    def on_request_start(self):
        ...

    def on_request_end(self):
        ...

    def on_validation_start(self):
        ...

    def on_validation_end(self):
        ...

    def on_parsing_start(self):
        ...

    def on_parsing_end(self):
        ...

    def resolve(self, _next, root, info: Info, *args, **kwargs):
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> Dict[str, Any]:
        return {}
