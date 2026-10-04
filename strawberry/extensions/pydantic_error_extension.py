import sys
from collections.abc import Iterator

from strawberry.extensions.base_extension import SchemaExtension


class PydanticErrorExtension(SchemaExtension):
    def on_operation(self) -> Iterator[None]:
        yield

        result = self.execution_context.result
        if not result or not result.errors:
            return

        # pydantic is optional and slow to import, so we don't import it unless
        # something else already did: if it was never imported, none of the
        # errors can be a pydantic ValidationError
        if sys.modules.get("pydantic") is None:
            return

        # an import (unlike reading sys.modules) waits for pydantic to be fully
        # initialized when another thread is still importing it
        try:
            from pydantic import ValidationError
        except ImportError:
            # e.g. a stub of pydantic, which can't have raised these errors
            return

        for error in result.errors:
            original_error = getattr(error, "original_error", None)

            if not isinstance(original_error, ValidationError):
                continue

            formatted = [
                {
                    "field": ".".join(map(str, err.get("loc", []))),
                    "message": err.get("msg", ""),
                }
                for err in original_error.errors()
            ]

            if not formatted:
                continue

            error.extensions = error.extensions or {}
            error.extensions["validation_errors"] = formatted
