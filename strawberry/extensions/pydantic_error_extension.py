from collections.abc import Iterator

from strawberry.extensions.base_extension import SchemaExtension

try:
    from pydantic import ValidationError as PydanticValidationError

    _PYDANTIC_AVAILABLE = True
except ImportError:
    _PYDANTIC_AVAILABLE = False


class PydanticErrorExtension(SchemaExtension):
    def on_operation(self) -> Iterator[None]:
        yield

        if not _PYDANTIC_AVAILABLE:
            return

        result = self.execution_context.result
        if not result or not result.errors:
            return

        for error in result.errors:
            original_error = getattr(error, "original_error", None)

            if not isinstance(original_error, PydanticValidationError):
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
