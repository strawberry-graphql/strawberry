from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
)

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.extensions.field_extension import (
    AsyncExtensionResolver,
    FieldExtension,
    SyncExtensionResolver,
)
from strawberry.field import StrawberryField
from strawberry.utils.str_converters import capitalize_first, to_camel_case

if TYPE_CHECKING:
    from strawberry.types.info import Info


class InputMutationExtension(FieldExtension):
    def apply(self, field: StrawberryField) -> None:
        resolver = field.base_resolver
        assert resolver

        name = field.graphql_name or to_camel_case(resolver.name)
        type_dict: Dict[str, Any] = {
            "__doc__": f"Input data for `{name}` mutation",
            "__annotations__": {},
        }
        annotations = resolver.wrapped_func.__annotations__

        for arg in resolver.arguments:
            arg_field = StrawberryField(
                python_name=arg.python_name,
                graphql_name=arg.graphql_name,
                description=arg.description,
                default=arg.default,
                type_annotation=arg.type_annotation,
                directives=tuple(arg.directives),
            )
            type_dict[arg_field.python_name] = arg_field
            type_dict["__annotations__"][arg_field.python_name] = annotations[
                arg.python_name
            ]

        caps_name = capitalize_first(name)
        new_type = strawberry.input(type(f"{caps_name}Input", (), type_dict))
        field.arguments = [
            StrawberryArgument(
                python_name="input",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    new_type,
                    namespace=resolver._namespace,
                ),
                description=type_dict["__doc__"],
            )
        ]

    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: Any,
    ) -> Any:
        input_args = kwargs.pop("input")
        return next_(
            source,
            info,
            **kwargs,
            **vars(input_args),
        )

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: Any,
    ) -> Any:
        input_args = kwargs.pop("input")
        return await next_(
            source,
            info,
            **kwargs,
            **vars(input_args),
        )
