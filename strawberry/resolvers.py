import enum
from inspect import iscoroutine
from typing import Any, Awaitable, Callable, Dict, List, Tuple, Union, cast

from .arguments import convert_arguments
from .field import FieldDefinition
from .types.fields.resolver import StrawberryResolver


def is_default_resolver(func: Callable) -> bool:
    """Check whether the function is a default resolver or a user provided one."""
    return getattr(func, "_is_default", False)


def convert_enums_to_values(field: FieldDefinition, result: Any) -> Any:
    # graphql-core expects a resolver for an Enum type to return
    # the enum's *value* (not its name or an instance of the enum).

    # short circut to skip checks when result is falsy
    if not result:
        return result

    if isinstance(result, enum.Enum):
        return result.value

    if field.is_list:
        child_type = cast(FieldDefinition, field.child)

        return [convert_enums_to_values(child_type, item) for item in result]

    return result


def get_arguments(
    field: FieldDefinition, kwargs: Dict[str, Any], source: Any, info: Any
) -> Tuple[List[Any], Dict[str, Any]]:
    actual_resolver = cast(StrawberryResolver, field.base_resolver)

    kwargs = convert_arguments(kwargs, field.arguments)

    # the following code allows to omit info and root arguments
    # by inspecting the original resolver arguments,
    # if it asks for self, the source will be passed as first argument
    # if it asks for root, the source it will be passed as kwarg
    # if it asks for info, the info will be passed as kwarg

    args = []

    if actual_resolver.has_self_arg:
        args.append(source)

    if actual_resolver.has_root_arg:
        kwargs["root"] = source

    if actual_resolver.has_info_arg:
        kwargs["info"] = info

    return args, kwargs


def get_result_for_field(
    field: FieldDefinition, kwargs: Dict[str, Any], source: Any, info: Any
) -> Union[Awaitable[Any], Any]:
    """
    Calls the resolver defined for `field`. If field doesn't have a
    resolver defined we default to using getattr on `source`.
    """

    actual_resolver = field.base_resolver

    if actual_resolver:
        args, kwargs = get_arguments(field, kwargs, source=source, info=info)

        return actual_resolver(*args, **kwargs)

    origin_name = cast(str, field.origin_name)
    return getattr(source, origin_name)


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

    async def _resolver_async(source, info, **kwargs):
        _check_permissions(source, info, **kwargs)

        result = get_result_for_field(field, kwargs=kwargs, info=info, source=source)

        if iscoroutine(result):  # pragma: no cover
            result = await result

        result = convert_enums_to_values(field, result)

        return result

    def _resolver(source, info, **kwargs):
        _check_permissions(source, info, **kwargs)

        result = get_result_for_field(field, kwargs=kwargs, info=info, source=source)
        result = convert_enums_to_values(field, result)

        return result

    _resolver_async._is_default = not field.base_resolver  # type: ignore
    _resolver._is_default = not field.base_resolver  # type: ignore

    return (
        _resolver_async
        if field.base_resolver and field.base_resolver.is_async
        else _resolver
    )
