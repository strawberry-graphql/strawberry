from asgiref.sync import sync_to_async

from strawberry.extensions import Extension


class SyncToAsync(Extension):
    def resolve(self, _next, root, info, *args, **kwargs):
        # If we are not executing in an async context then bail out early
        if not self.execution_context.is_async:
            return _next(root, info, *args, **kwargs)

        field = info.parent_type.fields[info.field_name]

        strawberry_field = field._strawberry_field

        if strawberry_field.base_resolver and not strawberry_field.is_async:
            return sync_to_async(_next)(root, info, *args, **kwargs)

        return _next(root, info, *args, **kwargs)
