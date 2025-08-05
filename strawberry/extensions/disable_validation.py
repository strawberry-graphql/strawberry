from collections.abc import Iterator

from strawberry.extensions.base_extension import SchemaExtension


class DisableValidation(SchemaExtension):
    """Disable query validation.

    Example:

    ```python
    import strawberry
    from strawberry.extensions import DisableValidation

    schema = strawberry.Schema(
        Query,
        extensions=[
            DisableValidation,
        ],
    )
    ```
    """

    def __init__(self) -> None:
        # There aren't any arguments to this extension yet but we might add
        # some in the future
        pass

    def on_operation(self) -> Iterator[None]:
        self.execution_context.validation_rules = ()  # remove all validation_rules
        yield


__all__ = ["DisableValidation"]
