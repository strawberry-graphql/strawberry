from strawberry.extensions.base_extension import Extension


class DisableValidation(Extension):
    """
    Disable query validation

    Example:

    >>> import strawberry
    >>> from strawberry.extensions import DisableValidation
    >>>
    >>> schema = strawberry.Schema(
    ...     Query,
    ...     extensions=[
    ...         DisableValidation(),
    ...     ]
    ... )

    """

    def __init__(self):
        # There aren't any arguments to this extension yet but we might add
        # some in the future
        pass

    def on_request_start(self) -> None:
        self.execution_context.validation_rules = ()  # remove all validation_rules
