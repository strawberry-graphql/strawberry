import dataclasses
import sys
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    overload,
)
from typing_extensions import Annotated, Literal, get_args, get_origin

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.field import _RESOLVER_TYPE
from strawberry.permission import BasePermission
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.info import Info
from strawberry.utils.str_converters import to_camel_case

from .fields import RelayField

_T = TypeVar("_T")


class InputMutationField(RelayField):
    """Relay Mutation field.

    Do not instantiate this directly. Instead, use `@relay.mutation`

    """

    default_args: Dict[str, StrawberryArgument] = {}

    def __call__(self, resolver: _RESOLVER_TYPE):
        name = to_camel_case(resolver.__name__)  # type: ignore[union-attr]
        cap_name = name[0].upper() + name[1:]
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
        new_type = strawberry.input(type(f"{cap_name}Input", (), type_dict))
        self.default_args["input"] = StrawberryArgument(
            python_name="input",
            graphql_name=None,
            type_annotation=StrawberryAnnotation(new_type, namespace=namespace),
            description=type_dict["__doc__"],
        )

        # FIXME: We need to set this after strawberry.input() or else it
        # will have problems with Annotated annotations for scalar types.
        # Find out why in the future...
        for f, annotation in f_types.items():
            f.type = annotation

        return super().__call__(resolver)

    @property
    def arguments(self) -> List[StrawberryArgument]:
        return list(self.default_args.values())

    def get_result(
        self,
        source: Any,
        info: Optional[Info],
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> Union[Awaitable[Any], Any]:
        assert self.base_resolver
        input_obj = kwargs.pop("input")
        return self.base_resolver(*args, **kwargs, **vars(input_obj))


@overload
def input_mutation(
    *,
    resolver: Callable[[], _T],
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
) -> _T:
    ...


@overload
def input_mutation(
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[True] = True,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
) -> Any:
    ...


@overload
def input_mutation(
    resolver: Union[StrawberryResolver, Callable, staticmethod, classmethod],
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
) -> InputMutationField:
    ...


def input_mutation(
    resolver=None,
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    # This init parameter is used by pyright to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False, None] = None,
) -> Any:
    """Annotate a property or a method to create an input mutation field.

    The difference from this mutation to the default one from strawberry is that
    all arguments found in the resolver will be converted to a single input type,
    named using the mutation name, capitalizing the first letter and append "Input"
    at the end. e.g. `doSomeMutation` will generate an input type `DoSomeMutationInput`.

    Examples:
        Annotating something like this:

        >>> @strawberry.type
        ... class CreateUserPayload:
        ...     user: UserType
        ...
        >>> @strawberry.mutation
        >>> class X:
        ...     @relay.input_mutation
        ...     def create_user(self, name: str, age: int) -> UserPayload:
        ...         ...

        Will create a type and an input type like

        ```
        input CreateUserInput {
            name: String!
            age: Int!
        }

        mutation {
            createUser (input: CreateUserInput!) {
                user: UserType
            }
        }
        ```

    """
    f = InputMutationField(
        python_name=None,
        graphql_name=name,
        type_annotation=None,
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        metadata=metadata,
        directives=directives or (),
    )
    if resolver is not None:
        f = f(resolver)
    return f
