from asgiref.sync import sync_to_async

from strawberry.extensions import Extension

from .utils import is_introspection_field


class SyncToAsync(Extension):
    """
    Wrap all custom resolvers in the `sync_to_async` decorator from
    `asgiref.sync` so that you can use the Django ORM in an async context.

    Example:
    >>> import strawberry
    >>> from strawberry.extensions import AddValidationRules
    >>>
    >>> @strawberry.type
    >>> class Query:
    ...     @strawberry.field
    ...     def latest_book_name(self) -> str:
    ...         return Book.objects.order_by("-created_at").first().name
    >>>
    >>> schema = strawberry.Schema(
    ...     Query,
    ...     extensions=[
    ...         SyncToAsync(),
    ...     ]
    ... )
    >>>
    >>> result = await schema.execute("{ latestBookName }")  # Works!
    """

    def __init__(self):
        # There aren't any arguments to this extension yet but we might add
        # some in the future
        pass

    def resolve(self, _next, root, info, *args, **kwargs):
        # If we are not executing in an async context then bail out early
        if not self.execution_context.is_async:
            return _next(root, info, *args, **kwargs)

        # Skip introspection fields
        if is_introspection_field(info):
            return _next(root, info, *args, **kwargs)

        field = info.parent_type.fields[info.field_name]

        strawberry_field = field._strawberry_field

        if strawberry_field.base_resolver and not strawberry_field.is_async:
            return sync_to_async(_next)(root, info, *args, **kwargs)

        return _next(root, info, *args, **kwargs)
