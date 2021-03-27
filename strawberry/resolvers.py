import enum
from inspect import iscoroutine
from typing import Any, Awaitable, Callable, Dict, List, Tuple, Union, cast

from graphql import GraphQLResolveInfo

from strawberry.types.info import Info

from .arguments import convert_arguments
from .field import StrawberryField
from .types.fields.resolver import StrawberryResolver


def is_default_resolver(func: Callable) -> bool:
    """Check whether the function is a default resolver or a user provided one."""
    return getattr(func, "_is_default", False)


def convert_enums_to_values(field: StrawberryField, result: Any) -> Any:
    # graphql-core expects a resolver for an Enum type to return
    # the enum's *value* (not its name or an instance of the enum).

    # short circuit to skip checks when result is falsy
    if not result:
        return result

    if isinstance(result, enum.Enum):
        return result.value

    if field.is_list:
        assert field.child is not None
        return [convert_enums_to_values(field.child, item) for item in result]

    return result


def get_arguments(
    field: StrawberryField, kwargs: Dict[str, Any], source: Any, info: Any
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
    field: StrawberryField, kwargs: Dict[str, Any], source: Any, info: Any
) -> Union[Awaitable[Any], Any]:
    """
    Calls the resolver defined for `field`. If field doesn't have a
    resolver defined we default to using getattr on `source`.
    """

    actual_resolver = field.base_resolver

    if actual_resolver:
        args, kwargs = get_arguments(field, kwargs, source=source, info=info)

        return actual_resolver(*args, **kwargs)

    return getattr(source, field.python_name)


def get_resolver(field: StrawberryField) -> Callable:
    # TODO: make sure that info is of type Info, currently it
    # is the value returned by graphql-core
    # https://github.com/strawberry-graphql/strawberry/issues/709
    def _check_permissions(source, info: Info, **kwargs):
        """
        Checks if the permission should be accepted and
        raises an exception if not
        """
        for permission_class in field.permission_classes:
            permission = permission_class()

            if not permission.has_permission(source, info, **kwargs):
                message = getattr(permission, "message", None)
                raise PermissionError(message)

    def _resolver(source, info: GraphQLResolveInfo, **kwargs):
        strawberry_info = strawberry_info_from_graphql(field, info)
        _check_permissions(source, strawberry_info, **kwargs)

        result = get_result_for_field(
            field, kwargs=kwargs, info=strawberry_info, source=source
        )

        if iscoroutine(result):  # pragma: no cover

            async def await_result(result):
                result = await result
                result = convert_enums_to_values(field, result)
                return result

            return await_result(result)

        result = convert_enums_to_values(field, result)
        return result

    _resolver._is_default = not field.base_resolver  # type: ignore
    return _resolver


def strawberry_info_from_graphql(
    field: FieldDefinition, info: GraphQLResolveInfo
) -> Info:
    return Info(
        field_name=info.field_name,
        context=info.context,
        root_value=info.root_value,
        variable_values=info.variable_values,
        return_type=field.type,
        operation=info.operation,
        path=info.path,
    )
