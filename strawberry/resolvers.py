import enum
from typing import Callable, cast

from .arguments import convert_arguments
from .field import FieldDefinition
from .utils.inspect import get_func_args


def is_default_resolver(func: Callable) -> bool:
    """Check whether the function is a default resolver or a user provided one."""
    return getattr(func, "_is_default", False)


def get_resolver(field: FieldDefinition) -> Callable:
    def _check_permissions(source, info, **kwargs):
        """
        Checks if the permission should be accepted and
        raises an exception if not
        """
        for permission_class in field.permission_classes:
            permission = permission_class()

            if not permission.has_permission(source, info, **kwargs):
                message = getattr(permission, "message", None)
                raise PermissionError(message)

    def _resolver(source, info, **kwargs):
        _check_permissions(source, info, **kwargs)

        actual_resolver = field.base_resolver

        if actual_resolver:
            kwargs = convert_arguments(kwargs, field.arguments)

            # the following code allows to omit info and root arguments
            # by inspecting the original resolver arguments,
            # if it asks for self, the source will be passed as first argument
            # if it asks for root, the source it will be passed as kwarg
            # if it asks for info, the info will be passed as kwarg

            function_args = get_func_args(actual_resolver)

            args = []

            if "self" in function_args:
                args.append(source)

            if "root" in function_args:
                kwargs["root"] = source

            if "info" in function_args:
                kwargs["info"] = info

            result = actual_resolver(*args, **kwargs)
        else:
            origin_name = cast(str, field.origin_name)
            result = getattr(source, origin_name)

        # graphql-core expects a resolver for an Enum type to return
        # the enum's *value* (not its name or an instance of the enum).
        if isinstance(result, enum.Enum):
            return result.value

        return result

    _resolver._is_default = not field.base_resolver  # type: ignore

    return _resolver
