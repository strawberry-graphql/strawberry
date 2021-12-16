from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast

from graphql import (
    GraphQLArgument,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLNullableType,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLScalarType,
    GraphQLType,
    GraphQLUnionType,
    Undefined,
)

from strawberry.arguments import UNSET, StrawberryArgument, convert_arguments, is_unset
from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
from strawberry.directive import StrawberryDirective
from strawberry.enum import EnumDefinition, EnumValue
from strawberry.exceptions import (
    MissingTypesForGenericError,
    ScalarAlreadyRegisteredError,
)
from strawberry.field import StrawberryField
from strawberry.lazy_type import LazyType
from strawberry.schema.config import StrawberryConfig
from strawberry.schema.types.scalar import _make_scalar_type
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType
from strawberry.types.info import Info
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion
from strawberry.utils.await_maybe import await_maybe

from . import compat
from .types.concrete_type import ConcreteType


# graphql-core expects a resolver for an Enum type to return
# the enum's *value* (not its name or an instance of the enum). We have to
# subclass the GraphQLEnumType class to enable returning Enum members from
# resolvers.
class CustomGraphQLEnumType(GraphQLEnumType):
    def serialize(self, output_value: Any) -> str:
        if isinstance(output_value, Enum):
            return output_value.name
        return super().serialize(output_value)


class GraphQLCoreConverter:
    # TODO: Make abstract

    def __init__(
        self,
        config: StrawberryConfig,
        scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]],
    ):
        self.type_map: Dict[str, ConcreteType] = {}
        self.config = config
        self.scalar_registry = scalar_registry

    def from_argument(self, argument: StrawberryArgument) -> GraphQLArgument:
        argument_type: GraphQLType

        if isinstance(argument.type, StrawberryOptional):
            argument_type = self.from_optional(argument.type)
        else:
            argument_type = self.from_non_optional(argument.type)

        default_value = Undefined if argument.default is UNSET else argument.default

        return GraphQLArgument(
            type_=argument_type,
            default_value=default_value,
            description=argument.description,
        )

    def from_enum(self, enum: EnumDefinition) -> CustomGraphQLEnumType:
        enum_name = self.config.name_converter.from_type(enum)

        assert enum_name is not None

        # Don't reevaluate known types
        if enum_name in self.type_map:
            graphql_enum = self.type_map[enum_name].implementation
            assert isinstance(graphql_enum, CustomGraphQLEnumType)  # For mypy
            return graphql_enum

        graphql_enum = CustomGraphQLEnumType(
            name=enum_name,
            values={item.name: self.from_enum_value(item) for item in enum.values},
            description=enum.description,
        )

        self.type_map[enum_name] = ConcreteType(
            definition=enum, implementation=graphql_enum
        )

        return graphql_enum

    def from_enum_value(self, enum_value: EnumValue) -> GraphQLEnumValue:
        return GraphQLEnumValue(enum_value.value)

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
        )

    def from_field(self, field: StrawberryField) -> GraphQLField:
        field_type: GraphQLType

        if isinstance(field.type, StrawberryOptional):
            field_type = self.from_optional(field.type)
        else:
            field_type = self.from_non_optional(field.type)

        resolver = self.from_resolver(field)
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
            extensions={"python_name": field.python_name},
        )

    def from_input_field(self, field: StrawberryField) -> GraphQLInputField:
        field_type: GraphQLType

        if isinstance(field.type, StrawberryOptional):
            field_type = self.from_optional(field.type)
        else:
            field_type = self.from_non_optional(field.type)

        default_value: object

        if is_unset(field.default_value):
            default_value = Undefined
        else:
            default_value = field.default_value

        return GraphQLInputField(
            type_=field_type,
            default_value=default_value,
            description=field.description,
        )

    def from_input_object(self, object_type: type) -> GraphQLInputObjectType:
        type_definition = object_type._type_definition  # type: ignore

        type_name = self.config.name_converter.from_type(type_definition)

        # Don't reevaluate known types
        if type_name in self.type_map:
            graphql_object_type = self.type_map[type_name].implementation
            assert isinstance(graphql_object_type, GraphQLInputObjectType)  # For mypy
            return graphql_object_type

        def get_graphql_fields() -> Dict[str, GraphQLInputField]:
            graphql_fields = {}
            for field in type_definition.fields:
                field_name = self.config.name_converter.from_field(field)

                graphql_fields[field_name] = self.from_input_field(field)

            return graphql_fields

        graphql_object_type = GraphQLInputObjectType(
            name=type_name,
            fields=get_graphql_fields,
            description=type_definition.description,
        )

        self.type_map[type_name] = ConcreteType(
            definition=type_definition, implementation=graphql_object_type
        )

        return graphql_object_type

    def from_interface(self, interface: TypeDefinition) -> GraphQLInterfaceType:
        # TODO: Use StrawberryInterface when it's implemented in another PR

        interface_name = self.config.name_converter.from_type(interface)

        # Don't reevaluate known types
        if interface_name in self.type_map:
            graphql_interface = self.type_map[interface_name].implementation
            assert isinstance(graphql_interface, GraphQLInterfaceType)  # For mypy
            return graphql_interface

        def get_graphql_fields() -> Dict[str, GraphQLField]:
            graphql_fields = {}

            for field in interface.fields:
                field_name = self.config.name_converter.from_field(field)
                graphql_fields[field_name] = self.from_field(field)

            return graphql_fields

        graphql_interface = GraphQLInterfaceType(
            name=interface_name,
            fields=get_graphql_fields,
            interfaces=list(map(self.from_interface, interface.interfaces)),
            description=interface.description,
        )

        self.type_map[interface_name] = ConcreteType(
            definition=interface, implementation=graphql_interface
        )

        return graphql_interface

    def from_list(self, type_: StrawberryList) -> GraphQLList:
        of_type: GraphQLType

        if isinstance(type_.of_type, StrawberryOptional):
            of_type = self.from_optional(type_.of_type)
        else:
            of_type = self.from_non_optional(type_.of_type)

        return GraphQLList(of_type)

    def from_optional(self, type_: StrawberryOptional) -> GraphQLNullableType:
        return self.from_type(type_.of_type)

    def from_non_optional(self, type_: Union[StrawberryType, type]) -> GraphQLNonNull:
        of_type = self.from_type(type_)
        return GraphQLNonNull(of_type)

    def from_object(self, object_type: TypeDefinition) -> GraphQLObjectType:
        # TODO: Use StrawberryObjectType when it's implemented in another PR
        object_type_name = self.config.name_converter.from_type(object_type)

        # Don't reevaluate known types
        if object_type_name in self.type_map:
            graphql_object_type = self.type_map[object_type_name].implementation
            assert isinstance(graphql_object_type, GraphQLObjectType)  # For mypy
            return graphql_object_type

        def get_graphql_fields() -> Dict[str, GraphQLField]:
            graphql_fields = {}

            for field in object_type.fields:
                field_name = self.config.name_converter.from_field(field)

                graphql_fields[field_name] = self.from_field(field)

            return graphql_fields

        is_type_of: Optional[Callable[[Any, GraphQLResolveInfo], bool]]
        if object_type.is_type_of:
            is_type_of = object_type.is_type_of
        elif object_type.interfaces:

            def is_type_of(obj: Any, _info: GraphQLResolveInfo) -> bool:
                return isinstance(obj, object_type.origin)

        else:
            is_type_of = None

        graphql_object_type = GraphQLObjectType(
            name=object_type_name,
            fields=get_graphql_fields,
            interfaces=list(map(self.from_interface, object_type.interfaces)),
            description=object_type.description,
            is_type_of=is_type_of,
        )

        self.type_map[object_type_name] = ConcreteType(
            definition=object_type, implementation=graphql_object_type
        )

        return graphql_object_type

    def from_resolver(
        self, field: StrawberryField
    ) -> Callable:  # TODO: Take StrawberryResolver
        def _get_arguments(
            source: Any,
            info: Info,
            kwargs: Dict[str, Any],
        ) -> Tuple[List[Any], Dict[str, Any]]:
            kwargs = convert_arguments(
                kwargs,
                field.arguments,
                scalar_registry=self.scalar_registry,
                config=self.config,
            )

            # the following code allows to omit info and root arguments
            # by inspecting the original resolver arguments,
            # if it asks for self, the source will be passed as first argument
            # if it asks for root, the source it will be passed as kwarg
            # if it asks for info, the info will be passed as kwarg

            args = []

            if field.base_resolver:
                if field.base_resolver.has_self_arg:
                    args.append(source)

                if field.base_resolver.has_root_arg:
                    kwargs["root"] = source

                if field.base_resolver.has_info_arg:
                    kwargs["info"] = info

            return args, kwargs

        def _check_permissions(source: Any, info: Info, kwargs: Dict[str, Any]):
            """
            Checks if the permission should be accepted and
            raises an exception if not
            """
            for permission_class in field.permission_classes:
                permission = permission_class()

                if not permission.has_permission(source, info, **kwargs):
                    message = getattr(permission, "message", None)
                    raise PermissionError(message)

        async def _check_permissions_async(
            source: Any, info: Info, kwargs: Dict[str, Any]
        ):
            for permission_class in field.permission_classes:
                permission = permission_class()
                has_permission: bool

                has_permission = await await_maybe(
                    permission.has_permission(source, info, **kwargs)
                )

                if not has_permission:
                    message = getattr(permission, "message", None)
                    raise PermissionError(message)

        def _strawberry_info_from_graphql(info: GraphQLResolveInfo) -> Info:
            return Info(
                _raw_info=info,
                _field=field,
            )

        def _get_result(_source: Any, info: Info, **kwargs):
            field_args, field_kwargs = _get_arguments(
                source=_source, info=info, kwargs=kwargs
            )

            return field.get_result(
                _source, info=info, args=field_args, kwargs=field_kwargs
            )

        def _resolver(_source: Any, info: GraphQLResolveInfo, **kwargs):
            strawberry_info = _strawberry_info_from_graphql(info)
            _check_permissions(_source, strawberry_info, kwargs)

            return _get_result(_source, strawberry_info, **kwargs)

        async def _async_resolver(_source: Any, info: GraphQLResolveInfo, **kwargs):
            strawberry_info = _strawberry_info_from_graphql(info)
            await _check_permissions_async(_source, strawberry_info, kwargs)

            return await await_maybe(_get_result(_source, strawberry_info, **kwargs))

        if field.is_async:
            _async_resolver._is_default = not field.base_resolver  # type: ignore
            return _async_resolver
        else:
            _resolver._is_default = not field.base_resolver  # type: ignore
            return _resolver

    def from_scalar(self, scalar: Type) -> GraphQLScalarType:
        scalar_definition: ScalarDefinition

        if scalar in self.scalar_registry:
            _scalar_definition = self.scalar_registry[scalar]
            if isinstance(_scalar_definition, ScalarWrapper):
                scalar_definition = _scalar_definition._scalar_definition
            else:
                scalar_definition = _scalar_definition
        else:
            scalar_definition = scalar._scalar_definition

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
            if self.type_map[scalar_name].definition != scalar_definition:
                raise ScalarAlreadyRegisteredError(scalar_name)

            implementation = cast(
                GraphQLScalarType, self.type_map[scalar_name].implementation
            )

        return implementation

    def from_type(self, type_: Union[StrawberryType, type]) -> GraphQLNullableType:
        if compat.is_generic(type_):
            raise MissingTypesForGenericError(type_)

        if isinstance(type_, EnumDefinition):  # TODO: Replace with StrawberryEnum
            return self.from_enum(type_)
        elif compat.is_input_type(type_):  # TODO: Replace with StrawberryInputObject
            return self.from_input_object(type_)
        elif isinstance(type_, StrawberryList):
            return self.from_list(type_)
        elif compat.is_interface_type(type_):  # TODO: Replace with StrawberryInterface
            type_definition: TypeDefinition = type_._type_definition  # type: ignore
            return self.from_interface(type_definition)
        elif compat.is_object_type(type_):  # TODO: Replace with StrawberryObject
            type_definition: TypeDefinition = type_._type_definition  # type: ignore
            return self.from_object(type_definition)
        elif compat.is_enum(type_):  # TODO: Replace with StrawberryEnum
            enum_definition: EnumDefinition = type_._enum_definition  # type: ignore
            return self.from_enum(enum_definition)
        elif isinstance(type_, TypeDefinition):  # TODO: Replace with StrawberryObject
            return self.from_object(type_)
        elif isinstance(type_, StrawberryUnion):
            return self.from_union(type_)
        elif isinstance(type_, LazyType):
            return self.from_type(type_.resolve_type())
        elif compat.is_scalar(
            type_, self.scalar_registry
        ):  # TODO: Replace with StrawberryScalar
            return self.from_scalar(type_)

        raise TypeError(f"Unexpected type '{type_}'")

    def from_union(self, union: StrawberryUnion) -> GraphQLUnionType:
        union_name = self.config.name_converter.from_type(union)

        # Don't reevaluate known types
        if union_name in self.type_map:
            graphql_union = self.type_map[union_name].implementation
            assert isinstance(graphql_union, GraphQLUnionType)  # For mypy
            return graphql_union

        graphql_types: List[GraphQLObjectType] = []
        for type_ in union.types:
            graphql_type = self.from_type(type_)

            assert isinstance(graphql_type, GraphQLObjectType)

            graphql_types.append(graphql_type)

        graphql_union = GraphQLUnionType(
            name=union_name,
            types=graphql_types,
            description=union.description,
            resolve_type=union.get_type_resolver(self.type_map),
        )

        self.type_map[union_name] = ConcreteType(
            definition=union, implementation=graphql_union
        )

        return graphql_union
