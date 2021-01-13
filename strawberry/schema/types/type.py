from typing import Type, Union, Any, Dict, Callable, cast

from graphql import GraphQLList, GraphQLType, GraphQLNullableType, GraphQLEnumType, \
    GraphQLEnumValue, GraphQLObjectType, GraphQLInterfaceType, GraphQLField, \
    GraphQLInputField, GraphQLInputObjectType, Undefined, GraphQLUnionType, \
    GraphQLScalarType, GraphQLArgument, GraphQLDirective, GraphQLNonNull, \
    GraphQLInputType, GraphQLOutputType

from strawberry.arguments import UNSET
from strawberry.directive import DirectiveDefinition
from strawberry.enum import EnumDefinition, EnumValue
from strawberry.field import FieldDefinition
from strawberry.resolvers import get_resolver
from strawberry.scalars import is_scalar
from strawberry.schema.types.directives import get_arguments_for_directive
from strawberry.types.types import ArgumentDefinition, undefined, TypeDefinition
from strawberry.union import StrawberryUnion

from .scalar import get_scalar_type
from .types import ConcreteType

FIELD_ARGUMENT_TYPE = Union[FieldDefinition, ArgumentDefinition]


class GraphQLCoreConverter:
    # TODO: Make abstract

    def __init__(self):
        self.type_map: Dict[str, ConcreteType] = {}

    def get_graphql_type_field(self, field: FIELD_ARGUMENT_TYPE) -> GraphQLType:
        # TODO: Completely replace with get_graphql_type

        graphql_type: GraphQLType

        if _is_list(field):
            graphql_type = self.from_list(field)
        elif _is_union(field):
            assert isinstance(field.type, StrawberryUnion)
            graphql_type = self.from_union(field.type)
        else:
            graphql_type = self.get_graphql_type(field.type)

        # TODO: Abstract this somehow. Logic is tricky
        if not _is_optional(field):
            graphql_type = cast(GraphQLNullableType, graphql_type)
            graphql_type = GraphQLNonNull(graphql_type)

        return graphql_type

    def get_graphql_type(self, type_: Any) -> GraphQLType:
        # TODO: Accept StrawberryType when implemented

        if _is_object_type(type_):
            if type_._type_definition.is_input:
                return self.from_input_object_type(type_)
            else:
                return self.from_object_type(type_)
        elif _is_enum(type_):
            return self.from_enum(type_)
        elif _is_scalar(type_):
            return self.from_scalar(type_)

        raise TypeError(f"Unexpected type '{type_}'")

    def from_argument(self, argument: ArgumentDefinition) -> GraphQLArgument:
        default_value = (
            Undefined
            if argument.default_value is undefined
            else argument.default_value
        )

        argument_type = self.get_graphql_type_field(argument)
        argument_type = cast(GraphQLInputType, argument_type)

        return GraphQLArgument(
            type_=argument_type,
            default_value=default_value,
            description=argument.description
        )

    def from_enum(self, enum: EnumDefinition) -> GraphQLEnumType:

        assert enum.name is not None

        return GraphQLEnumType(
            name=enum.name,
            values={
                item.name: self.from_enum_value(item) for item in enum.values
            },
            description=enum.description
        )

    def from_enum_value(self, enum_value: EnumValue) -> GraphQLEnumValue:
        return GraphQLEnumValue(enum_value.value)

    def from_directive(self, directive: DirectiveDefinition) -> GraphQLDirective:
        arguments = get_arguments_for_directive(directive.resolver)

        graphql_arguments = {}
        for argument in arguments:
            assert argument.name is not None
            graphql_arguments[argument.name] = self.from_argument(argument)

        return GraphQLDirective(
            name=directive.name,
            locations=directive.locations,
            args=graphql_arguments,
            description=directive.description
        )

    def from_field(self, field: FieldDefinition) -> GraphQLField:

        # This shouldn't be used here. Messes up conversion hierarchy
        field_type = self.get_graphql_type_field(field)
        field_type = cast(GraphQLOutputType, field_type)

        resolver = self.from_resolver(field)
        subscribe = None

        if field.is_subscription:
            subscribe = resolver
            resolver = lambda event, *_, **__: event

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
            deprecation_reason=field.deprecation_reason
        )

    def from_input_field(self, field: FieldDefinition) -> GraphQLInputField:
        if field.default_value in [undefined, UNSET]:
            default_value = Undefined
        else:
            default_value = field.default_value

        field_type = self.get_graphql_type_field(field)
        field_type = cast(GraphQLInputType, field_type)

        return GraphQLInputField(
            type_=field_type,
            default_value=default_value,
            description=field.description
        )

    def from_input_object_type(self, object_type: Type) -> GraphQLInputObjectType:
        if not hasattr(object_type, "_type_definition"):
            raise TypeError(f"Wrong type passed to get object type: {object_type}")

        type_definition = object_type._type_definition

        if not type_definition.is_input:
            raise TypeError(f"{object_type} is not an input type")

        return GraphQLInputObjectType(
            name=type_definition.name,
            # TODO: Does this need to be deferred?
            fields={
                field.name: self.from_input_field(field)
                for field in type_definition.fields
            },
            description=type_definition.description,
        )

    def from_interface(self, interface: TypeDefinition) -> GraphQLInterfaceType:
        # TODO: Use StrawberryInterface when it's implemented in another PR

        graphql_fields = {}
        for field in interface.fields:
            assert field.name is not None
            graphql_fields[field.name] = self.from_field(field)

        return GraphQLInterfaceType(
            name=interface.name,
            fields=graphql_fields,
            interfaces=list(map(self.from_interface, interface.interfaces)),
            description=interface.description,
        )

    def from_list(self, list_: FIELD_ARGUMENT_TYPE) -> GraphQLList:
        assert list_.child is not None
        of_type = self.get_graphql_type_field(list_.child)

        return GraphQLList(of_type)

    def from_object_type(self, object_type: Type) -> GraphQLObjectType:
        # TODO: Use StrawberryObjectType when it's implemented in another PR
        if not hasattr(object_type, "_type_definition"):
            raise TypeError(f"Wrong type passed to get object type {object_type}")

        type_definition = object_type._type_definition

        # Don't reevaluate known types
        if type_definition.name in self.type_map:
            graphql_object_type = self.type_map[type_definition.name].implementation
            assert isinstance(graphql_object_type, GraphQLObjectType)
            return graphql_object_type

        graphql_object_type = GraphQLObjectType(
            name=type_definition.name,
            fields=lambda: {
                field.name: self.from_field(field)
                for field in type_definition.fields
            },
            interfaces=list(map(self.from_interface, type_definition.interfaces)),
            is_type_of=lambda obj, _: isinstance(obj, type_definition.origin),
            description=type_definition.description,
        )

        self.type_map[type_definition.name] = ConcreteType(
            definition=type_definition, implementation=graphql_object_type
        )

        return graphql_object_type

    def from_resolver(self, field: FieldDefinition) -> Callable:
        # TODO: Take in StrawberryResolver
        return get_resolver(field)

    def from_scalar(self, scalar: Type) -> GraphQLScalarType:
        return get_scalar_type(scalar, self.type_map)

    def from_union(self, union: StrawberryUnion) -> GraphQLUnionType:
        raise NotImplementedError
        # return get_union_type(union, type_map)


################################################################################
# Temporary functions to be removed with new types
################################################################################


def _is_list(field: FIELD_ARGUMENT_TYPE) -> bool:
    # isinstance(type_, StrawberryList)
    return field.is_list


def _is_optional(field: FIELD_ARGUMENT_TYPE) -> bool:
    # isinstance(type_, StrawberryOptional)
    return field.is_optional


def _is_union(field: FIELD_ARGUMENT_TYPE) -> bool:
    # isinstance(type_, StrawberryUnion)
    return field.is_union


def _is_scalar(type_: Type) -> bool:
    # isinstance(type_, StrawberryScalar)
    return is_scalar(type_)


def _is_object_type(type_: Type) -> bool:
    # isinstance(type_, StrawberryObjectType)
    return hasattr(type_, "_type_definition")


def _is_enum(type_: Type) -> bool:
    # isinstance(type_, StrawberryEnum)
    return hasattr(type_, "_enum_definition")
