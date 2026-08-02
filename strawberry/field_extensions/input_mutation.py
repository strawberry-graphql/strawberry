from __future__ import annotations

from typing import Any

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.extensions.field_extension import FieldExtension
from strawberry.types.arguments import StrawberryArgument
from strawberry.types.field import StrawberryField
from strawberry.utils.str_converters import capitalize_first, to_camel_case


class InputMutationExtension(FieldExtension):
    def apply(self, field: StrawberryField) -> None:
        resolver = field.base_resolver
        assert resolver

        name = field.graphql_name or to_camel_case(resolver.name)
        type_dict: dict[str, Any] = {
            "__doc__": f"Input data for `{name}` mutation",
            "__annotations__": {},
        }
        annotations = resolver.wrapped_func.__annotations__

        for arg in resolver.arguments:
            arg_field = StrawberryField(
                python_name=arg.python_name,
                graphql_name=arg.graphql_name,
                description=arg.description,
                deprecation_reason=arg.deprecation_reason,
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

    def map_arguments(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        # Unpack the generated ``input`` object into the resolver's individual
        # keyword arguments, so the resolver keeps its original signature.
        input_args = kwargs.pop("input")
        return {**kwargs, **vars(input_args)}


__all__ = ["InputMutationExtension"]
