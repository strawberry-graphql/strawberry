from __future__ import annotations

from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    TypeVar,
)
from typing_extensions import Annotated, get_args, get_origin

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.extensions.field_extension import (
    AsyncExtensionResolver,
    FieldExtension,
    SyncExtensionResolver,
)
from strawberry.utils.str_converters import to_camel_case

from .field import StrawberryField, field

if TYPE_CHECKING:
    from strawberry.types.info import Info

_T = TypeVar("_T")


class InputMutationExtension(FieldExtension):
    def apply(self, field: StrawberryField) -> None:
        resolver = field.base_resolver
        assert resolver

        name = field.graphql_name or to_camel_case(resolver.name)
        name_captalized = name[0].upper() + name[1:]
        type_dict: Dict[str, Any] = {
            "__doc__": f"Input data for `{name}` mutation",
            "__annotations__": {},
        }
        annotations = resolver.wrapped_func.__annotations__

        for arg in resolver.arguments:
            # Preserve directives
            annotation = annotations[arg.python_name]
            if get_origin(annotation) is Annotated:
                directives = tuple(
                    d
                    for d in get_args(annotation)[1:]
                    if hasattr(d, "__strawberry_directive__")
                )
            else:
                directives = ()

            arg_field = StrawberryField(
                python_name=arg.python_name,
                graphql_name=arg.graphql_name,
                description=arg.description,
                default=arg.default,
                type_annotation=arg.type_annotation,
                directives=directives,
            )
            type_dict[arg_field.python_name] = arg_field
            type_dict["__annotations__"][arg_field.python_name] = annotation

        caps_name = name[0].upper() + name[1:]
        new_type = strawberry.input(type(f"{caps_name}Input", (), type_dict))
        field.default_arguments.append(
            StrawberryArgument(
                python_name="input",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    new_type,
                    namespace=resolver._namespace,
                ),
                description=type_dict["__doc__"],
            )
        )
        field.ignore_resolver_arguments = True

    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs,
    ) -> Any:
        input_args = kwargs.pop("input")
        return next_(
            source,
            info,
            **kwargs,
            **input_args,
        )

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs,
    ) -> Any:
        input_args = kwargs.pop("input")
        return await next_(
            source,
            info,
            **kwargs,
            **input_args,
        )


# Mutations and subscriptions are field, we might want to separate
# things in the long run for example to provide better errors
mutation = field
subscription = partial(field, is_subscription=True)

if TYPE_CHECKING:
    input_mutation = field
else:

    def input_mutation(*args, **kwargs) -> StrawberryField:
        kwargs["extensions"] = [*kwargs.get("extensions", []), InputMutationExtension()]
        return field(*args, **kwargs)
