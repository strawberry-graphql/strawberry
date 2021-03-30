from typing import Any, Callable, Dict, Type, cast

from graphql import (
    GraphQLArgument,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLNullableType,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLType,
    GraphQLUnionType,
    Undefined,
)

from strawberry.arguments import UNSET
from strawberry.directive import DirectiveDefinition
from strawberry.enum import EnumDefinition, EnumValue
from strawberry.field import StrawberryField
from strawberry.scalars import is_scalar
from strawberry.types.types import ArgumentDefinition, TypeDefinition, undefined
from strawberry.union import StrawberryUnion

from .types.concrete_type import ConcreteType
from .types.scalar import get_scalar_type


class GraphQLCoreConverter:
    # TODO: Make abstract

    def __init__(self):
        self.type_map: Dict[str, ConcreteType] = {}

    def get_graphql_type_argument(self, argument: ArgumentDefinition) -> GraphQLType:
        # TODO: Completely replace with get_graphql_type

        graphql_type: GraphQLType

        if argument.is_list:
            graphql_type = self.from_list_argument(argument)
        elif argument.is_union:
            assert isinstance(argument.type, StrawberryUnion)  # For mypy
            graphql_type = self.from_union(argument.type)
        else:
            graphql_type = self.get_graphql_type(argument.type)

        # TODO: Abstract this somehow. Logic is tricky
        if not argument.is_optional:
            graphql_type = cast(GraphQLNullableType, graphql_type)
            graphql_type = GraphQLNonNull(graphql_type)

        return graphql_type

    def get_graphql_type_field(self, field: StrawberryField) -> GraphQLType:
        # TODO: Completely replace with get_graphql_type

        graphql_type: GraphQLType

        if field.is_list:
            graphql_type = self.from_list_field(field)
        elif field.is_union:
            assert isinstance(field.type, StrawberryUnion)  # For mypy
            graphql_type = self.from_union(field.type)
        else:
            graphql_type = self.get_graphql_type(field.type)

        # TODO: Abstract this somehow. Logic is tricky
        if not field.is_optional:
            graphql_type = cast(GraphQLNullableType, graphql_type)
            graphql_type = GraphQLNonNull(graphql_type)

        return graphql_type

    def get_graphql_type(self, type_: Any) -> GraphQLType:
        # TODO: Accept StrawberryType when implemented

        if _is_object_type(type_):
            if type_._type_definition.is_input:
                return self.from_input_object_type(type_)
            elif type_._type_definition.is_interface:
                return self.from_interface(type_._type_definition)
            else:
                return self.from_object_type(type_)
        elif _is_enum(type_):
            return self.from_enum(type_._enum_definition)
        elif _is_scalar(type_):
            return self.from_scalar(type_)

        raise TypeError(f"Unexpected type '{type_}'")

    def from_argument(self, argument: ArgumentDefinition) -> GraphQLArgument:
        default_value = (
            Undefined if argument.default_value is undefined else argument.default_value
        )

        argument_type = self.get_graphql_type_argument(argument)
        argument_type = cast(GraphQLInputType, argument_type)

        return GraphQLArgument(
            type_=argument_type,
            default_value=default_value,
            description=argument.description,
        )

    def from_enum(self, enum: EnumDefinition) -> GraphQLEnumType:

        assert enum.name is not None

        # Don't reevaluate known types
        if enum.name in self.type_map:
            graphql_enum = self.type_map[enum.name].implementation
            assert isinstance(graphql_enum, GraphQLEnumType)  # For mypy
            return graphql_enum

        graphql_enum = GraphQLEnumType(
            name=enum.name,
            values={item.name: self.from_enum_value(item) for item in enum.values},
            description=enum.description,
        )

        self.type_map[enum.name] = ConcreteType(
            definition=enum, implementation=graphql_enum
        )

        return graphql_enum

    def from_enum_value(self, enum_value: EnumValue) -> GraphQLEnumValue:
        return GraphQLEnumValue(enum_value.value)

    def from_directive(self, directive: DirectiveDefinition) -> GraphQLDirective:

        graphql_arguments = {}
        for argument in directive.arguments:
            assert argument.name is not None
            graphql_arguments[argument.name] = self.from_argument(argument)

        return GraphQLDirective(
            name=directive.name,
            locations=directive.locations,
            args=graphql_arguments,
            description=directive.description,
        )

    def from_field(self, field: StrawberryField) -> GraphQLField:

        field_type = self.get_graphql_type_field(field)
        field_type = cast(GraphQLOutputType, field_type)

        resolver = self.from_resolver(field)
        subscribe = None

        if field.is_subscription:
            subscribe = resolver
            resolver = lambda event, *_, **__: event  # noqa: E731

        graphql_arguments = {}
        for argument in field.arguments:
            assert argument.name is not None
            graphql_arguments[argument.name] = self.from_argument(argument)

        return GraphQLField(
            type_=field_type,
            args=graphql_arguments,
            resolve=resolver,
            subscribe=subscribe,
            description=field.description,
            deprecation_reason=field.deprecation_reason,
        )

    def from_input_field(self, field: StrawberryField) -> GraphQLInputField:
        if field.default_value in [undefined, UNSET]:
            default_value = Undefined
        else:
            default_value = field.default_value

        field_type = self.get_graphql_type_field(field)
        field_type = cast(GraphQLInputType, field_type)

        return GraphQLInputField(
            type_=field_type, default_value=default_value, description=field.description
        )

    def from_input_object_type(self, object_type: Type) -> GraphQLInputObjectType:
        type_definition = object_type._type_definition

        # Don't reevaluate known types
        if type_definition.name in self.type_map:
            graphql_object_type = self.type_map[type_definition.name].implementation
            assert isinstance(graphql_object_type, GraphQLInputObjectType)  # For mypy
            return graphql_object_type

        def get_graphql_fields() -> Dict[str, GraphQLInputField]:
            graphql_fields = {}
            for field in type_definition.fields:
                assert field.graphql_name is not None
                graphql_fields[field.graphql_name] = self.from_input_field(field)
            return graphql_fields

        graphql_object_type = GraphQLInputObjectType(
            name=type_definition.name,
            fields=get_graphql_fields,
            description=type_definition.description,
        )

        self.type_map[type_definition.name] = ConcreteType(
            definition=type_definition, implementation=graphql_object_type
        )

        return graphql_object_type

    def from_interface(self, interface: TypeDefinition) -> GraphQLInterfaceType:
        # TODO: Use StrawberryInterface when it's implemented in another PR

        # Don't reevaluate known types
        if interface.name in self.type_map:
            graphql_interface = self.type_map[interface.name].implementation
            assert isinstance(graphql_interface, GraphQLInterfaceType)  # For mypy
            return graphql_interface

        def get_graphql_fields() -> Dict[str, GraphQLField]:
            graphql_fields = {}
            for field in interface.fields:
                assert field.graphql_name is not None
                graphql_fields[field.graphql_name] = self.from_field(field)
            return graphql_fields

        graphql_interface = GraphQLInterfaceType(
            name=interface.name,
            fields=get_graphql_fields,
            interfaces=list(map(self.from_interface, interface.interfaces)),
            description=interface.description,
        )

        self.type_map[interface.name] = ConcreteType(
            definition=interface, implementation=graphql_interface
        )

        return graphql_interface

    def from_list_argument(self, list_: ArgumentDefinition) -> GraphQLList:
        assert list_.child is not None
        of_type = self.get_graphql_type_argument(list_.child)

        return GraphQLList(of_type)

    def from_list_field(self, list_: StrawberryField) -> GraphQLList:
        assert list_.child is not None
        of_type = self.get_graphql_type_field(list_.child)

        return GraphQLList(of_type)

    def from_object_type(self, object_type: Type) -> GraphQLObjectType:
        # TODO: Use StrawberryObjectType when it's implemented in another PR

        type_definition = object_type._type_definition

        # Don't reevaluate known types
        if type_definition.name in self.type_map:
            graphql_object_type = self.type_map[type_definition.name].implementation
            assert isinstance(graphql_object_type, GraphQLObjectType)  # For mypy
            return graphql_object_type

        # Only define an is_type_of function for Types that implement an interface.
        # Otherwise, leave it to the default implementation
        is_type_of = (
            (lambda obj, _: isinstance(obj, type_definition.origin))
            if type_definition.interfaces
            else None
        )

        def get_graphql_fields() -> Dict[str, GraphQLField]:
            graphql_fields = {}
            for field in type_definition.fields:
                assert field.graphql_name is not None
                graphql_fields[field.graphql_name] = self.from_field(field)
            return graphql_fields

        graphql_object_type = GraphQLObjectType(
            name=type_definition.name,
            fields=get_graphql_fields,
            interfaces=list(map(self.from_interface, type_definition.interfaces)),
            is_type_of=is_type_of,
            description=type_definition.description,
        )

        self.type_map[type_definition.name] = ConcreteType(
            definition=type_definition, implementation=graphql_object_type
        )

        return graphql_object_type

    def from_resolver(self, field: StrawberryField) -> Callable:
        return field.get_wrapped_resolver()

    def from_scalar(self, scalar: Type) -> GraphQLScalarType:
        return get_scalar_type(scalar, self.type_map)

    def from_union(self, union: StrawberryUnion) -> GraphQLUnionType:

        # Don't reevaluate known types
        if union.name in self.type_map:
            graphql_union = self.type_map[union.name].implementation
            assert isinstance(graphql_union, GraphQLUnionType)  # For mypy
            return graphql_union

        graphql_types = []
        for type_ in union.types:
            graphql_type = self.get_graphql_type(type_)
            assert isinstance(graphql_type, GraphQLObjectType)  # For mypy
            graphql_types.append(graphql_type)

        graphql_union = GraphQLUnionType(
            name=union.name,
            types=graphql_types,
            description=union.description,
            resolve_type=union.get_type_resolver(self.type_map),
        )

        self.type_map[union.name] = ConcreteType(
            definition=union, implementation=graphql_union
        )

        return graphql_union


################################################################################
# Temporary functions to be removed with new types
################################################################################


def _is_scalar(type_: Type) -> bool:
    # isinstance(type_, StrawberryScalar)  # noqa: E800
    return is_scalar(type_)


def _is_object_type(type_: Type) -> bool:
    # isinstance(type_, StrawberryObjectType)  # noqa: E800
    return hasattr(type_, "_type_definition")


def _is_enum(type_: Type) -> bool:
    # isinstance(type_, StrawberryEnum)  # noqa: E800
    return hasattr(type_, "_enum_definition")
