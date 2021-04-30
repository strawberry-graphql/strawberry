from typing import Callable, Dict, Type

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
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
    Undefined, GraphQLNullableType, GraphQLNonNull,
)

from strawberry.arguments import UNSET, StrawberryArgument
from strawberry.directive import DirectiveDefinition
from strawberry.enum import EnumDefinition, EnumValue
from strawberry.field import StrawberryField
from strawberry.scalars import is_scalar
from strawberry.type import StrawberryOptional, StrawberryType, StrawberryList
from strawberry.types.types import TypeDefinition, undefined
from strawberry.union import StrawberryUnion

from .types.concrete_type import ConcreteType
from .types.scalar import get_scalar_type


class GraphQLCoreConverter:
    # TODO: Make abstract

    def __init__(self):
        self.type_map: Dict[str, ConcreteType] = {}

    def from_argument(self, argument: StrawberryArgument) -> GraphQLArgument:
        if isinstance(argument.type, StrawberryOptional):
            argument_type = self.from_optional(argument.type)
        else:
            argument_type = self.from_non_optional(argument.type)

        default_value = (
            Undefined if argument.default_value is undefined else argument.default_value
        )

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
            assert argument.graphql_name is not None
            graphql_arguments[argument.graphql_name] = self.from_argument(argument)

        return GraphQLDirective(
            name=directive.name,
            locations=directive.locations,
            args=graphql_arguments,
            description=directive.description,
        )

    def from_field(self, field: StrawberryField) -> GraphQLField:

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
            assert argument.graphql_name is not None
            graphql_arguments[argument.graphql_name] = self.from_argument(argument)

        return GraphQLField(
            type_=field_type,
            args=graphql_arguments,
            resolve=resolver,
            subscribe=subscribe,
            description=field.description,
            deprecation_reason=field.deprecation_reason,
        )

    def from_input_field(self, field: StrawberryField) -> GraphQLInputField:
        if isinstance(field.type, StrawberryOptional):
            field_type = self.from_optional(field.type)
        else:
            field_type = self.from_non_optional(field.type)

        if field.default_value in [undefined, UNSET]:
            default_value = Undefined
        else:
            default_value = field.default_value

        return GraphQLInputField(
            type_=field_type,
            default_value=default_value,
            description=field.description,
        )

    def from_input_object(self, object_type: Type) -> GraphQLInputObjectType:
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

    def from_list(self, type_: StrawberryList) -> GraphQLList:
        if isinstance(type_.of_type, StrawberryOptional):
            of_type = self.from_optional(type_.of_type)
        else:
            of_type = self.from_non_optional(type_.of_type)

        return GraphQLList(of_type)

    def from_optional(self, type_: StrawberryOptional) -> GraphQLNullableType:
        return self.from_type(type_.of_type)

    def from_non_optional(self, type_: StrawberryType) -> GraphQLNonNull:
        of_type = self.from_type(type_)
        return GraphQLNonNull(of_type)

    def from_object(self, object_type: Type) -> GraphQLObjectType:
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

    def from_resolver(self, field: StrawberryField) -> Callable:  # TODO: Take StrawberryResolver
        return field.get_wrapped_resolver()

    def from_scalar(self, scalar: Type) -> GraphQLScalarType:
        return get_scalar_type(scalar, self.type_map)

    def from_type(self, type_: StrawberryType) -> GraphQLNullableType:
        if isinstance(type_, EnumDefinition):  # TODO: Replace with StrawberryEnum
            return self.from_enum(type_)
        # elif isinstance(evaled_type, StrawberryInterface):
        #     return True
        elif _is_input_type(type_):  # TODO: Replace with StrawberryInputObject
            return self.from_input_object(type_)
        elif isinstance(type_, StrawberryList):
            return self.from_list(type_)
        elif _is_object_type(type_):  # TODO: Replace with StrawberryObject
            return self.from_object(type_)
        elif isinstance(type_, StrawberryOptional):
            # TODO: Not sure how to handle just yet
            raise NotImplementedError()
        elif _is_scalar(type_):  # TODO: Replace with StrawberryScalar
            return self.from_scalar(type_)
        elif isinstance(type, StrawberryUnion):
            return self.from_union(type_)

        raise TypeError(f"Unexpected type '{type_}'")

    def from_union(self, union: StrawberryUnion) -> GraphQLUnionType:

        # Don't reevaluate known types
        if union.name in self.type_map:
            graphql_union = self.type_map[union.name].implementation
            assert isinstance(graphql_union, GraphQLUnionType)  # For mypy
            return graphql_union

        graphql_types = []
        for type_ in union.types:
            graphql_type = self.from_type(type_)
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


def _is_input_type(type_: Type) -> bool:
    if not _is_object_type(type_):
        return False

    return type_._type_definition.is_input


def _is_scalar(type_: Type) -> bool:
    # isinstance(type_, StrawberryScalar)  # noqa: E800
    return is_scalar(type_)


def _is_object_type(type_: Type) -> bool:
    # isinstance(type_, StrawberryObjectType)  # noqa: E800
    return hasattr(type_, "_type_definition")
