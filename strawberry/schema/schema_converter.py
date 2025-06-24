from __future__ import annotations

import dataclasses
import sys
from functools import partial, reduce
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
    cast,
)
from typing_extensions import Protocol

from graphql import (
    GraphQLAbstractType,
    GraphQLArgument,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLError,
    GraphQLField,
    GraphQLID,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLType,
    GraphQLUnionType,
    Undefined,
    ValueNode,
    default_type_resolver,
)
from graphql.language.directive_locations import DirectiveLocation

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    DuplicatedTypeName,
    InvalidTypeInputForUnion,
    InvalidUnionTypeError,
    MissingTypesForGenericError,
    ScalarAlreadyRegisteredError,
    UnresolvedFieldTypeError,
)
from strawberry.extensions.field_extension import build_field_extension_resolvers
from strawberry.relay.types import GlobalID
from strawberry.schema.types.scalar import (
    DEFAULT_SCALAR_REGISTRY,
    _get_scalar_definition,
    _make_scalar_type,
)
from strawberry.types.arguments import StrawberryArgument, convert_arguments
from strawberry.types.base import (
    StrawberryList,
    StrawberryMaybe,
    StrawberryObjectDefinition,
    StrawberryOptional,
    StrawberryType,
    get_object_definition,
    has_object_definition,
)
from strawberry.types.cast import get_strawberry_type_cast
from strawberry.types.enum import EnumDefinition
from strawberry.types.field import UNRESOLVED
from strawberry.types.lazy_type import LazyType
from strawberry.types.private import is_private
from strawberry.types.scalar import ScalarWrapper, scalar
from strawberry.types.union import StrawberryUnion
from strawberry.types.unset import UNSET
from strawberry.utils.await_maybe import await_maybe

from . import compat
from .types.concrete_type import ConcreteType

if TYPE_CHECKING:
    from collections.abc import Awaitable, Mapping

    from graphql import (
        GraphQLInputType,
        GraphQLNullableType,
        GraphQLOutputType,
        GraphQLResolveInfo,
    )

    from strawberry.directive import StrawberryDirective
    from strawberry.schema.config import StrawberryConfig
    from strawberry.schema_directive import StrawberrySchemaDirective
    from strawberry.types.enum import EnumValue
    from strawberry.types.field import StrawberryField
    from strawberry.types.info import Info
    from strawberry.types.scalar import ScalarDefinition


FieldType = TypeVar(
    "FieldType",
    bound=Union[GraphQLField, GraphQLInputField],
    covariant=True,
)


class FieldConverterProtocol(Generic[FieldType], Protocol):
    def __call__(  # pragma: no cover
        self,
        field: StrawberryField,
        *,
        type_definition: Optional[StrawberryObjectDefinition] = None,
    ) -> FieldType: ...


def _get_thunk_mapping(
    type_definition: StrawberryObjectDefinition,
    name_converter: Callable[[StrawberryField], str],
    field_converter: FieldConverterProtocol[FieldType],
    get_fields: Callable[[StrawberryObjectDefinition], list[StrawberryField]],
) -> dict[str, FieldType]:
    """Create a GraphQL core `ThunkMapping` mapping of field names to field types.

    This method filters out remaining `strawberry.Private` annotated fields that
    could not be filtered during the initialization of a `TypeDefinition` due to
    postponed type-hint evaluation (PEP-563). Performing this filtering now (at
    schema conversion time) ensures that all types to be included in the schema
    should have already been resolved.

    Raises:
        TypeError: If the type of a field in ``fields`` is `UNRESOLVED`
    """
    thunk_mapping: dict[str, FieldType] = {}

    fields = get_fields(type_definition)

    for field in fields:
        field_type = field.type

        if field_type is UNRESOLVED:
            raise UnresolvedFieldTypeError(type_definition, field)

        if not is_private(field_type):
            thunk_mapping[name_converter(field)] = field_converter(
                field,
                type_definition=type_definition,
            )

    return thunk_mapping


# graphql-core expects a resolver for an Enum type to return
# the enum's *value* (not its name or an instance of the enum). We have to
# subclass the GraphQLEnumType class to enable returning Enum members from
# resolvers.
class CustomGraphQLEnumType(GraphQLEnumType):
    def __init__(
        self,
        enum: EnumDefinition,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.wrapped_cls = enum.wrapped_cls

    def serialize(self, output_value: Any) -> str:
        if isinstance(output_value, self.wrapped_cls):
            for name, value in self.values.items():
                if output_value.value == value.value:
                    return name

            raise ValueError(
                f"Invalid value for enum {self.name}: {output_value}"
            )  # pragma: no cover

        return super().serialize(output_value)

    def parse_value(self, input_value: str) -> Any:
        return self.wrapped_cls(super().parse_value(input_value))

    def parse_literal(
        self, value_node: ValueNode, _variables: Optional[dict[str, Any]] = None
    ) -> Any:
        return self.wrapped_cls(super().parse_literal(value_node, _variables))


def get_arguments(
    *,
    field: StrawberryField,
    source: Any,
    info: Info,
    kwargs: Any,
    config: StrawberryConfig,
    scalar_registry: Mapping[object, Union[ScalarWrapper, ScalarDefinition]],
) -> tuple[list[Any], dict[str, Any]]:
    # TODO: An extension might have changed the resolver arguments,
    # but we need them here since we are calling it.
    # This is a bit of a hack, but it's the easiest way to get the arguments
    # This happens in mutation.InputMutationExtension
    field_arguments = field.arguments[:]
    if field.base_resolver:
        existing = {arg.python_name for arg in field_arguments}
        field_arguments.extend(
            [
                arg
                for arg in field.base_resolver.arguments
                if arg.python_name not in existing
            ]
        )

    kwargs = convert_arguments(
        kwargs,
        field_arguments,
        scalar_registry=scalar_registry,
        config=config,
    )

    # the following code allows to omit info and root arguments
    # by inspecting the original resolver arguments,
    # if it asks for self, the source will be passed as first argument
    # if it asks for root or parent, the source will be passed as kwarg
    # if it asks for info, the info will be passed as kwarg

    args = []

    if field.base_resolver:
        if field.base_resolver.self_parameter:
            args.append(source)

        if parent_parameter := field.base_resolver.parent_parameter:
            kwargs[parent_parameter.name] = source

        if root_parameter := field.base_resolver.root_parameter:
            kwargs[root_parameter.name] = source

        if info_parameter := field.base_resolver.info_parameter:
            kwargs[info_parameter.name] = info

    return args, kwargs


class GraphQLCoreConverter:
    # TODO: Make abstract

    # Extension key used to link a GraphQLType back into the Strawberry definition
    DEFINITION_BACKREF = "strawberry-definition"

    def __init__(
        self,
        config: StrawberryConfig,
        scalar_overrides: Mapping[object, Union[ScalarWrapper, ScalarDefinition]],
        get_fields: Callable[[StrawberryObjectDefinition], list[StrawberryField]],
    ) -> None:
        self.type_map: dict[str, ConcreteType] = {}
        self.config = config
        self.scalar_registry = self._get_scalar_registry(scalar_overrides)
        self.get_fields = get_fields

    def _get_scalar_registry(
        self,
        scalar_overrides: Mapping[object, Union[ScalarWrapper, ScalarDefinition]],
    ) -> Mapping[object, Union[ScalarWrapper, ScalarDefinition]]:
        scalar_registry = {**DEFAULT_SCALAR_REGISTRY}

        global_id_name = "GlobalID" if self.config.relay_use_legacy_global_id else "ID"

        scalar_registry[GlobalID] = _get_scalar_definition(
            scalar(
                GlobalID,
                name=global_id_name,
                description=GraphQLID.description,
                parse_value=lambda v: v,
                serialize=str,
                specified_by_url=("https://relay.dev/graphql/objectidentification.htm"),
            )
        )

        if scalar_overrides:
            # TODO: check that the overrides are valid
            scalar_registry.update(scalar_overrides)  # type: ignore

        return scalar_registry

    def from_argument(self, argument: StrawberryArgument) -> GraphQLArgument:
        argument_type = cast(
            "GraphQLInputType", self.from_maybe_optional(argument.type)
        )
        if argument.is_maybe:
            default_value: Any = Undefined
        else:
            default_value = Undefined if argument.default is UNSET else argument.default

        return GraphQLArgument(
            type_=argument_type,
            default_value=default_value,
            description=argument.description,
            deprecation_reason=argument.deprecation_reason,
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: argument,
            },
        )

    def from_enum(self, enum: EnumDefinition) -> CustomGraphQLEnumType:
        enum_name = self.config.name_converter.from_type(enum)

        assert enum_name is not None

        # Don't reevaluate known types
        cached_type = self.type_map.get(enum_name, None)
        if cached_type:
            self.validate_same_type_definition(enum_name, enum, cached_type)
            graphql_enum = cached_type.implementation
            assert isinstance(graphql_enum, CustomGraphQLEnumType)  # For mypy
            return graphql_enum

        graphql_enum = CustomGraphQLEnumType(
            enum=enum,
            name=enum_name,
            values={
                self.config.name_converter.from_enum_value(
                    enum, item
                ): self.from_enum_value(item)
                for item in enum.values
            },
            description=enum.description,
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: enum,
            },
        )

        self.type_map[enum_name] = ConcreteType(
            definition=enum, implementation=graphql_enum
        )

        return graphql_enum

    def from_enum_value(self, enum_value: EnumValue) -> GraphQLEnumValue:
        return GraphQLEnumValue(
            enum_value.value,
            deprecation_reason=enum_value.deprecation_reason,
            description=enum_value.description,
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: enum_value,
            },
        )

    def from_directive(self, directive: StrawberryDirective) -> GraphQLDirective:
        graphql_arguments = {}

        for argument in directive.arguments:
            argument_name = self.config.name_converter.from_argument(argument)
            graphql_arguments[argument_name] = self.from_argument(argument)

        directive_name = self.config.name_converter.from_type(directive)

        return GraphQLDirective(
            name=directive_name,
            locations=directive.locations,
            args=graphql_arguments,
            description=directive.description,
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: directive,
            },
        )

    def from_schema_directive(self, cls: type) -> GraphQLDirective:
        strawberry_directive = cast(
            "StrawberrySchemaDirective",
            cls.__strawberry_directive__,  # type: ignore[attr-defined]
        )
        module = sys.modules[cls.__module__]

        args: dict[str, GraphQLArgument] = {}
        for field in strawberry_directive.fields:
            default = field.default
            if default == dataclasses.MISSING:
                default = UNSET

            name = self.config.name_converter.get_graphql_name(field)
            args[name] = self.from_argument(
                StrawberryArgument(
                    python_name=field.python_name or field.name,
                    graphql_name=None,
                    type_annotation=StrawberryAnnotation(
                        annotation=field.type,
                        namespace=module.__dict__,
                    ),
                    default=default,
                )
            )

        return GraphQLDirective(
            name=self.config.name_converter.from_directive(strawberry_directive),
            locations=[
                DirectiveLocation(loc.value) for loc in strawberry_directive.locations
            ],
            args=args,
            is_repeatable=strawberry_directive.repeatable,
            description=strawberry_directive.description,
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: strawberry_directive,
            },
        )

    def from_field(
        self,
        field: StrawberryField,
        *,
        type_definition: Optional[StrawberryObjectDefinition] = None,
    ) -> GraphQLField:
        # self.from_resolver needs to be called before accessing field.type because
        # in there a field extension might want to change the type during its apply
        resolver = self.from_resolver(field)
        field_type = cast(
            "GraphQLOutputType",
            self.from_maybe_optional(
                field.resolve_type(type_definition=type_definition)
            ),
        )
        subscribe = None

        if field.is_subscription:
            subscribe = resolver
            resolver = lambda event, *_, **__: event  # noqa: E731

        graphql_arguments = {}
        for argument in field.arguments:
            argument_name = self.config.name_converter.from_argument(argument)
            graphql_arguments[argument_name] = self.from_argument(argument)

        return GraphQLField(
            type_=field_type,
            args=graphql_arguments,
            resolve=resolver,
            subscribe=subscribe,
            description=field.description,
            deprecation_reason=field.deprecation_reason,
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: field,
            },
        )

    def from_input_field(
        self,
        field: StrawberryField,
        *,
        type_definition: Optional[StrawberryObjectDefinition] = None,
    ) -> GraphQLInputField:
        field_type = cast(
            "GraphQLInputType",
            self.from_maybe_optional(
                field.resolve_type(type_definition=type_definition)
            ),
        )
        default_value: object
        if isinstance(field.type, StrawberryMaybe):
            default_value = Undefined
        elif field.default_value is UNSET or field.default_value is dataclasses.MISSING:
            default_value = Undefined
        else:
            default_value = field.default_value

        return GraphQLInputField(
            type_=field_type,
            default_value=default_value,
            description=field.description,
            deprecation_reason=field.deprecation_reason,
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: field,
            },
        )

    def get_graphql_fields(
        self, type_definition: StrawberryObjectDefinition
    ) -> dict[str, GraphQLField]:
        return _get_thunk_mapping(
            type_definition=type_definition,
            name_converter=self.config.name_converter.from_field,
            field_converter=self.from_field,
            get_fields=self.get_fields,
        )

    def get_graphql_input_fields(
        self, type_definition: StrawberryObjectDefinition
    ) -> dict[str, GraphQLInputField]:
        return _get_thunk_mapping(
            type_definition=type_definition,
            name_converter=self.config.name_converter.from_field,
            field_converter=self.from_input_field,
            get_fields=self.get_fields,
        )

    def from_input_object(self, object_type: type) -> GraphQLInputObjectType:
        type_definition = object_type.__strawberry_definition__  # type: ignore

        type_name = self.config.name_converter.from_type(type_definition)

        # Don't reevaluate known types
        cached_type = self.type_map.get(type_name, None)
        if cached_type:
            self.validate_same_type_definition(type_name, type_definition, cached_type)
            graphql_object_type = self.type_map[type_name].implementation
            assert isinstance(graphql_object_type, GraphQLInputObjectType)  # For mypy
            return graphql_object_type

        def check_one_of(value: dict[str, Any]) -> dict[str, Any]:
            if len(value) != 1:
                raise GraphQLError(
                    f"OneOf Input Object '{type_name}' must specify exactly one key."
                )

            first_key, first_value = next(iter(value.items()))

            if first_value is None or first_value is UNSET:
                raise GraphQLError(
                    f"Value for member field '{first_key}' must be non-null"
                )

            return value

        out_type = (
            check_one_of
            if type_definition.is_input and type_definition.is_one_of
            else None
        )

        graphql_object_type = GraphQLInputObjectType(
            name=type_name,
            fields=lambda: self.get_graphql_input_fields(type_definition),
            description=type_definition.description,
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: type_definition,
            },
            out_type=out_type,
        )

        self.type_map[type_name] = ConcreteType(
            definition=type_definition, implementation=graphql_object_type
        )

        return graphql_object_type

    def from_interface(
        self, interface: StrawberryObjectDefinition
    ) -> GraphQLInterfaceType:
        interface_name = self.config.name_converter.from_type(interface)

        # Don't re-evaluate known types
        cached_type = self.type_map.get(interface_name, None)
        if cached_type:
            self.validate_same_type_definition(interface_name, interface, cached_type)
            graphql_interface = cached_type.implementation
            assert isinstance(graphql_interface, GraphQLInterfaceType)  # For mypy
            return graphql_interface

        def _get_resolve_type() -> Callable[
            [Any, GraphQLResolveInfo, GraphQLAbstractType],
            Union[Awaitable[Optional[str]], str, None],
        ]:
            if interface.resolve_type:
                return interface.resolve_type

            def resolve_type(
                obj: Any, info: GraphQLResolveInfo, abstract_type: GraphQLAbstractType
            ) -> Union[Awaitable[Optional[str]], str, None]:
                if isinstance(obj, interface.origin):
                    type_definition = get_object_definition(obj, strict=True)

                    # TODO: we should find the correct type here from the
                    # generic
                    if not type_definition.is_graphql_generic:
                        return type_definition.name

                    # here we don't all the implementations of the generic
                    # we need to find a way to find them, for now maybe
                    # we can follow the union's approach and iterate over
                    # all the types in the schema, but we should probably
                    # optimize this

                    return_type: Optional[GraphQLType] = None

                    for possible_concrete_type in self.type_map.values():
                        possible_type = possible_concrete_type.definition

                        if not isinstance(
                            possible_type, StrawberryObjectDefinition
                        ):  # pragma: no cover
                            continue

                        if possible_type.is_implemented_by(obj):
                            return_type = possible_concrete_type.implementation
                            break

                    if return_type:
                        assert isinstance(return_type, GraphQLNamedType)

                        return return_type.name

                # Revert to calling is_type_of for cases where a direct subclass
                # of the interface is not returned (i.e. an ORM object)
                return default_type_resolver(obj, info, abstract_type)

            return resolve_type

        graphql_interface = GraphQLInterfaceType(
            name=interface_name,
            fields=lambda: self.get_graphql_fields(interface),
            interfaces=list(map(self.from_interface, interface.interfaces)),
            description=interface.description,
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: interface,
            },
            resolve_type=_get_resolve_type(),
        )

        self.type_map[interface_name] = ConcreteType(
            definition=interface, implementation=graphql_interface
        )

        return graphql_interface

    def from_list(self, type_: StrawberryList) -> GraphQLList:
        of_type = self.from_maybe_optional(type_.of_type)

        return GraphQLList(of_type)

    def from_object(self, object_type: StrawberryObjectDefinition) -> GraphQLObjectType:
        # TODO: Use StrawberryObjectType when it's implemented in another PR
        object_type_name = self.config.name_converter.from_type(object_type)

        # Don't reevaluate known types
        cached_type = self.type_map.get(object_type_name, None)
        if cached_type:
            self.validate_same_type_definition(
                object_type_name, object_type, cached_type
            )
            graphql_object_type = cached_type.implementation
            assert isinstance(graphql_object_type, GraphQLObjectType)  # For mypy
            return graphql_object_type

        def _get_is_type_of() -> Optional[Callable[[Any, GraphQLResolveInfo], bool]]:
            if object_type.is_type_of:
                return object_type.is_type_of

            if not object_type.interfaces:
                return None

            # this allows returning interfaces types as well as the actual object type
            # this is useful in combination with `resolve_type` in interfaces
            possible_types = (
                *tuple(interface.origin for interface in object_type.interfaces),
                object_type.origin,
            )

            def is_type_of(obj: Any, _info: GraphQLResolveInfo) -> bool:
                if (type_cast := get_strawberry_type_cast(obj)) is not None:
                    return type_cast in possible_types

                if object_type.concrete_of and (
                    has_object_definition(obj)
                    and obj.__strawberry_definition__.origin
                    is object_type.concrete_of.origin
                ):
                    return True

                return isinstance(obj, possible_types)

            return is_type_of

        graphql_object_type = GraphQLObjectType(
            name=object_type_name,
            fields=lambda: self.get_graphql_fields(object_type),
            interfaces=list(map(self.from_interface, object_type.interfaces)),
            description=object_type.description,
            is_type_of=_get_is_type_of(),
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: object_type,
            },
        )

        self.type_map[object_type_name] = ConcreteType(
            definition=object_type, implementation=graphql_object_type
        )

        return graphql_object_type

    def from_resolver(
        self, field: StrawberryField
    ) -> Callable:  # TODO: Take StrawberryResolver
        field.default_resolver = self.config.default_resolver

        if field.is_basic_field:

            def _get_basic_result(_source: Any, *args: str, **kwargs: Any) -> Any:
                # Call `get_result` without an info object or any args or
                # kwargs because this is a basic field with no resolver.
                return field.get_result(_source, info=None, args=[], kwargs={})

            _get_basic_result._is_default = True  # type: ignore

            return _get_basic_result

        def _strawberry_info_from_graphql(info: GraphQLResolveInfo) -> Info:
            return self.config.info_class(
                _raw_info=info,
                _field=field,
            )

        def _get_result(
            _source: Any,
            info: Info,
            field_args: list[Any],
            field_kwargs: dict[str, Any],
        ) -> Any:
            return field.get_result(
                _source, info=info, args=field_args, kwargs=field_kwargs
            )

        def wrap_field_extensions() -> Callable[..., Any]:
            """Wrap the provided field resolver with the middleware."""
            for extension in field.extensions:
                extension.apply(field)

            extension_functions = build_field_extension_resolvers(field)

            def extension_resolver(
                _source: Any,
                info: Info,
                **kwargs: Any,
            ) -> Any:
                # parse field arguments into Strawberry input types and convert
                # field names to Python equivalents
                field_args, field_kwargs = get_arguments(
                    field=field,
                    source=_source,
                    info=info,
                    kwargs=kwargs,
                    config=self.config,
                    scalar_registry=self.scalar_registry,
                )

                resolver_requested_info = False
                if "info" in field_kwargs:
                    resolver_requested_info = True
                    # remove info from field_kwargs because we're passing it
                    # explicitly to the extensions
                    field_kwargs.pop("info")

                # `_get_result` expects `field_args` and `field_kwargs` as
                # separate arguments so we have to wrap the function so that we
                # can pass them in
                def wrapped_get_result(_source: Any, info: Info, **kwargs: Any) -> Any:
                    # if the resolver function requested the info object info
                    # then put it back in the kwargs dictionary
                    if resolver_requested_info:
                        kwargs["info"] = info

                    return _get_result(
                        _source, info, field_args=field_args, field_kwargs=kwargs
                    )

                # combine all the extension resolvers
                return reduce(
                    lambda chained_fn, next_fn: partial(next_fn, chained_fn),
                    extension_functions,
                    wrapped_get_result,
                )(_source, info, **field_kwargs)

            return extension_resolver

        _get_result_with_extensions = wrap_field_extensions()

        def _resolver(_source: Any, info: GraphQLResolveInfo, **kwargs: Any) -> Any:
            strawberry_info = _strawberry_info_from_graphql(info)

            return _get_result_with_extensions(
                _source,
                strawberry_info,
                **kwargs,
            )

        async def _async_resolver(
            _source: Any, info: GraphQLResolveInfo, **kwargs: Any
        ) -> Any:
            strawberry_info = _strawberry_info_from_graphql(info)

            return await await_maybe(
                _get_result_with_extensions(
                    _source,
                    strawberry_info,
                    **kwargs,
                )
            )

        if field.is_async:
            _async_resolver._is_default = not field.base_resolver  # type: ignore
            return _async_resolver
        _resolver._is_default = not field.base_resolver  # type: ignore
        return _resolver

    def from_scalar(self, scalar: type) -> GraphQLScalarType:
        from strawberry.relay.types import GlobalID

        if not self.config.relay_use_legacy_global_id and scalar is GlobalID:
            from strawberry import ID

            return self.from_scalar(ID)

        scalar_definition: ScalarDefinition

        if scalar in self.scalar_registry:
            _scalar_definition = self.scalar_registry[scalar]
            # TODO: check why we need the cast and we are not trying with getattr first
            if isinstance(_scalar_definition, ScalarWrapper):
                scalar_definition = _scalar_definition._scalar_definition
            else:
                scalar_definition = _scalar_definition
        else:
            scalar_definition = scalar._scalar_definition  # type: ignore[attr-defined]

        scalar_name = self.config.name_converter.from_type(scalar_definition)

        if scalar_name not in self.type_map:
            implementation = (
                scalar_definition.implementation
                if scalar_definition.implementation is not None
                else _make_scalar_type(scalar_definition)
            )

            self.type_map[scalar_name] = ConcreteType(
                definition=scalar_definition, implementation=implementation
            )
        else:
            other_definition = self.type_map[scalar_name].definition

            # TODO: the other definition might not be a scalar, we should
            # handle this case better, since right now we assume it is a scalar

            if other_definition != scalar_definition:
                other_definition = cast("ScalarDefinition", other_definition)

                raise ScalarAlreadyRegisteredError(scalar_definition, other_definition)

            implementation = cast(
                "GraphQLScalarType", self.type_map[scalar_name].implementation
            )

        return implementation

    def from_maybe_optional(
        self, type_: Union[StrawberryType, type]
    ) -> Union[GraphQLNullableType, GraphQLNonNull]:
        NoneType = type(None)
        if type_ is None or type_ is NoneType:
            return self.from_type(type_)
        if isinstance(type_, StrawberryOptional):
            return self.from_type(type_.of_type)
        return GraphQLNonNull(self.from_type(type_))

    def from_type(self, type_: Union[StrawberryType, type]) -> GraphQLNullableType:
        if compat.is_graphql_generic(type_):
            raise MissingTypesForGenericError(type_)

        if isinstance(type_, EnumDefinition):  # TODO: Replace with StrawberryEnum
            return self.from_enum(type_)
        if compat.is_input_type(type_):  # TODO: Replace with StrawberryInputObject
            return self.from_input_object(type_)
        if isinstance(type_, StrawberryList):
            return self.from_list(type_)
        if compat.is_interface_type(type_):  # TODO: Replace with StrawberryInterface
            type_definition: StrawberryObjectDefinition = (
                type_.__strawberry_definition__  # type: ignore
            )
            return self.from_interface(type_definition)
        if has_object_definition(type_):
            return self.from_object(type_.__strawberry_definition__)
        if compat.is_enum(type_):  # TODO: Replace with StrawberryEnum
            enum_definition: EnumDefinition = type_._enum_definition  # type: ignore
            return self.from_enum(enum_definition)
        if isinstance(type_, StrawberryObjectDefinition):
            return self.from_object(type_)
        if isinstance(type_, StrawberryUnion):
            return self.from_union(type_)
        if isinstance(type_, LazyType):
            return self.from_type(type_.resolve_type())
        if compat.is_scalar(
            type_, self.scalar_registry
        ):  # TODO: Replace with StrawberryScalar
            return self.from_scalar(type_)

        raise TypeError(f"Unexpected type '{type_}'")

    def from_union(self, union: StrawberryUnion) -> GraphQLUnionType:
        union_name = self.config.name_converter.from_type(union)

        for type_ in union.types:
            # This check also occurs in the Annotation resolving, but because of
            # TypeVars, Annotations, LazyTypes, etc it can't perfectly detect issues at
            # that stage
            if not StrawberryUnion.is_valid_union_type(type_):
                raise InvalidUnionTypeError(union_name, type_, union_definition=union)

        # Don't re-evaluate known types
        if union_name in self.type_map:
            graphql_union = self.type_map[union_name].implementation
            assert isinstance(graphql_union, GraphQLUnionType)  # For mypy
            return graphql_union

        graphql_types: list[GraphQLObjectType] = []

        for type_ in union.types:
            graphql_type = self.from_type(type_)

            if isinstance(graphql_type, GraphQLInputObjectType):
                raise InvalidTypeInputForUnion(graphql_type)
            assert isinstance(graphql_type, (GraphQLObjectType, GraphQLUnionType))

            # If the graphql_type is a GraphQLUnionType, merge its child types
            if isinstance(graphql_type, GraphQLUnionType):
                # Add the child types of the GraphQLUnionType to the list of graphql_types,
                # filter out any duplicates
                for child_type in graphql_type.types:
                    if child_type not in graphql_types:
                        graphql_types.append(child_type)
            else:
                graphql_types.append(graphql_type)

        graphql_union = GraphQLUnionType(
            name=union_name,
            types=graphql_types,
            description=union.description,
            resolve_type=union.get_type_resolver(self.type_map),
            extensions={
                GraphQLCoreConverter.DEFINITION_BACKREF: union,
            },
        )

        self.type_map[union_name] = ConcreteType(
            definition=union, implementation=graphql_union
        )

        return graphql_union

    def _get_is_type_of(
        self,
        object_type: StrawberryObjectDefinition,
    ) -> Optional[Callable[[Any, GraphQLResolveInfo], bool]]:
        if object_type.is_type_of:
            return object_type.is_type_of

        if object_type.interfaces:

            def is_type_of(obj: Any, _info: GraphQLResolveInfo) -> bool:
                if (type_cast := get_strawberry_type_cast(obj)) is not None:
                    return type_cast is object_type.origin

                if object_type.concrete_of and (
                    has_object_definition(obj)
                    and obj.__strawberry_definition__.origin
                    is object_type.concrete_of.origin
                ):
                    return True

                return isinstance(obj, object_type.origin)

            return is_type_of

        return None

    def validate_same_type_definition(
        self, name: str, type_definition: StrawberryType, cached_type: ConcreteType
    ) -> None:
        # Skip validation if _unsafe_disable_same_type_validation is True
        if (
            self.config._unsafe_disable_same_type_validation
            or cached_type.definition == type_definition
        ):
            return

        # otherwise we need to check if we are dealing with different instances
        # of the same type generic type. This happens when using the same generic
        # type in different places in the schema, like in the following example:

        # >>> @strawberry.type
        # >>> class A(Generic[T]):
        # >>>     a: T

        # >>> @strawberry.type
        # >>> class Query:
        # >>>     first: A[int]
        # >>>     second: A[int]

        # in theory we won't ever have duplicated definitions for the same generic,
        # but we are doing the check in an exhaustive way just in case we missed
        # something.

        # we only do this check for TypeDefinitions, as they are the only ones
        # that can be generic.
        # of they are of the same generic type, we need to check if the type
        # var map is the same, in that case we can return

        first_type_definition = cached_type.definition
        second_type_definition = type_definition

        # TODO: maybe move this on the StrawberryType class
        if (
            isinstance(first_type_definition, StrawberryObjectDefinition)
            and isinstance(second_type_definition, StrawberryObjectDefinition)
            and first_type_definition.concrete_of is not None
            and first_type_definition.concrete_of == second_type_definition.concrete_of
            and (
                first_type_definition.type_var_map.keys()
                == second_type_definition.type_var_map.keys()
            )
        ):
            # manually compare type_var_maps while resolving any lazy types
            # so that they're considered equal to the actual types they're referencing
            equal = True
            for type_var, type1 in first_type_definition.type_var_map.items():
                type2 = second_type_definition.type_var_map[type_var]
                # both lazy types are always resolved because two different lazy types
                # may be referencing the same actual type
                if isinstance(type1, LazyType):
                    type1 = type1.resolve_type()  # noqa: PLW2901
                elif isinstance(type1, StrawberryOptional) and isinstance(
                    type1.of_type, LazyType
                ):
                    type1.of_type = type1.of_type.resolve_type()

                if isinstance(type2, LazyType):
                    type2 = type2.resolve_type()
                elif isinstance(type2, StrawberryOptional) and isinstance(
                    type2.of_type, LazyType
                ):
                    type2.of_type = type2.of_type.resolve_type()

                if type1 != type2:
                    equal = False
                    break
            if equal:
                return

        if isinstance(second_type_definition, StrawberryObjectDefinition):
            first_origin = second_type_definition.origin
        elif isinstance(second_type_definition, EnumDefinition):
            first_origin = second_type_definition.wrapped_cls
        else:
            first_origin = None

        if isinstance(first_type_definition, StrawberryObjectDefinition):
            second_origin = first_type_definition.origin
        elif isinstance(first_type_definition, EnumDefinition):
            second_origin = first_type_definition.wrapped_cls
        else:
            second_origin = None

        raise DuplicatedTypeName(first_origin, second_origin, name)


__all__ = ["GraphQLCoreConverter"]
