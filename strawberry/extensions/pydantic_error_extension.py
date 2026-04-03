from strawberry.extensions import SchemaExtension


class PydanticErrorExtension(SchemaExtension):
    def on_operation(self):
        yield

        result = self.execution_context.result
        if not result or not result.errors:
            return

        for error in result.errors:
            original_error = getattr(error, "original_error", None)

            # Detect Pydantic-style errors via `.errors()` method
            if original_error and hasattr(original_error, "errors"):
                try:
                    raw_errors = original_error.errors()
                except Exception:
                    continue

                if raw_errors:
                    formatted = [
                        {
                            "field": ".".join(str(x) for x in err.get("loc", [])),
                            "message": err.get("msg", ""),
                        }
                        for err in raw_errors
                    ]

                    error.extensions = error.extensions or {}
                    error.extensions["validation_errors"] = formatted