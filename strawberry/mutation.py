from __future__ import annotations

import sys
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
)
from typing_extensions import Annotated, get_args, get_origin

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.utils.str_converters import to_camel_case

from .field import _RESOLVER_TYPE, StrawberryField, field

if TYPE_CHECKING:
    from strawberry.types.info import Info

_T = TypeVar("_T")


class StrawberryInputMutationField(StrawberryField):
    """Relay Mutation field.

    Do not instantiate this directly. Instead, use `@relay.mutation`

    """

    def __init__(self, *args, **kwargs):
        self._args = {}
        super().__init__(*args, **kwargs)

    def __call__(self, resolver: _RESOLVER_TYPE):
        name = to_camel_case(resolver.__name__)  # type: ignore[union-attr]
        caps_name = name[0].upper() + name[1:]
        namespace = sys.modules[resolver.__module__].__dict__
        annotations = resolver.__annotations__
        resolver = StrawberryResolver(resolver)

        args = resolver.arguments
        type_dict: Dict[str, Any] = {
            "__doc__": f"Input data for `{name}` mutation",
            "__annotations__": {},
        }
        f_types = {}
        for arg in args:
            annotation = annotations[arg.python_name]
            if get_origin(annotation) is Annotated:
                directives = tuple(
                    d
                    for d in get_args(annotation)[1:]
                    if hasattr(d, "__strawberry_directive__")
                )
            else:
                directives = ()

            type_dict["__annotations__"][arg.python_name] = annotation
            arg_field = strawberry.field(
                name=arg.graphql_name,
                is_subscription=arg.is_subscription,
                description=arg.description,
                default=arg.default,
                directives=directives,
            )
            arg_field.graphql_name = arg.graphql_name
            f_types[arg_field] = arg.type_annotation
            type_dict[arg.python_name] = arg_field

        # TODO: We are not creating a type for the output payload, as it is not easy to
        # do that with the typing system. Is there a way to solve that automatically?
        new_type = strawberry.input(type(f"{caps_name}Input", (), type_dict))
        self._args["input"] = StrawberryArgument(
            python_name="input",
            graphql_name=None,
            type_annotation=StrawberryAnnotation(new_type, namespace=namespace),
            description=type_dict["__doc__"],
        )

        # FIXME: We need to set this after strawberry.input() or else it
        # will have problems with Annotated annotations for scalar types.
        # Find out why...
        for f, annotation in f_types.items():
            f.type = annotation

        return super().__call__(resolver)

    @property
    def arguments(self) -> List[StrawberryArgument]:
        return list(self._args.values())

    @property
    def is_basic_field(self):
        return False

    def get_result(
        self,
        source: Any,
        info: Optional[Info],
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> Union[Awaitable[Any], Any]:
        assert self.base_resolver
        input_obj = kwargs.pop("input")
        return self.base_resolver(
            *args,
            **kwargs,
            **vars(input_obj),
        )


# Mutations and subscriptions are field, we might want to separate
# things in the long run for example to provide better errors
mutation = field
input_mutation = partial(field, field_class=StrawberryInputMutationField)
subscription = partial(field, is_subscription=True)
