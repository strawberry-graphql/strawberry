from typing import Optional, Type, Union, Any, Dict, Callable

from graphql import GraphQLList, GraphQLType, GraphQLNullableType, GraphQLEnumType, \
    GraphQLEnumValue, GraphQLObjectType, GraphQLInterfaceType, GraphQLField, \
    GraphQLInputField, GraphQLInputObjectType, Undefined, GraphQLUnionType, \
    GraphQLScalarType, GraphQLArgument, GraphQLDirective, GraphQLNonNull, \
    GraphQLInputType
from typing_extensions import TypeAlias

from strawberry.arguments import UNSET
from strawberry.directive import DirectiveDefinition
from strawberry.field import FieldDefinition
from strawberry.resolvers import get_resolver
from strawberry.scalars import is_scalar
from strawberry.schema.types.directives import get_arguments_for_directive
from strawberry.types.types import ArgumentDefinition, undefined, TypeDefinition
from strawberry.union import StrawberryUnion

from .enum import get_enum_type
from .scalar import get_scalar_type
from .types import TypeMap, ConcreteType
from .union import get_union_type


# Temporary until we have real types

FIELD_ARGUMENT_TYPE: TypeAlias = Union[FieldDefinition, ArgumentDefinition]
# StrawberryObjectType: TypeAlias = Any


def get_type_for_annotation(annotation: Type, type_map: TypeMap) -> GraphQLType:
    graphql_type: Optional[GraphQLType] = None

    # this adds support for type annotations that use
    # strings, without having to use get_type_hints

    if type(annotation) == str and annotation in type_map:
        return type_map[annotation].implementation  # type: ignore

    if is_scalar(annotation):
        graphql_type = get_scalar_type(annotation, type_map)

    elif hasattr(annotation, "_enum_definition"):
        graphql_type = get_enum_type(annotation._enum_definition, type_map)
    elif hasattr(annotation, "_type_definition"):
        from .object_type import get_object_type

        graphql_type = get_object_type(annotation, type_map)

    if not graphql_type:
        raise ValueError(f"Unable to get GraphQL type for {annotation}")

    return graphql_type


def get_graphql_type(field: FIELD_ARGUMENT_TYPE, type_map: TypeMap) -> GraphQLType:
    return GraphQLCoreConverter.get_graphql_type_field(field, type_map)
    # # by default fields in GraphQL-Core are optional, but for us we only want
    # # to mark optional fields when they are inside a Optional type hint
    # wrap: Optional[Callable] = GraphQLNonNull
    #
    # type: GraphQLType
    # field_type = cast(Type, field.type)
    #
    # if field.is_optional:
    #     wrap = None
    #
    # if field.is_list:
    #     child = cast(FieldDefinition, field.child)
    #     type = GraphQLList(get_graphql_type(child, type_map))
    #
    # elif field.is_union:
    #     union_definition = cast(StrawberryUnion, field_type)
    #     type = get_union_type(union_definition, type_map)
    # else:
    #     type = get_type_for_annotation(field_type, type_map)
    #
    # if wrap:
    #     return wrap(type)
    #
    # return type


class GraphQLCoreConverter:
    # TODO: Make abstract

    def __init__(self):
        self.type_map: Dict[str, ConcreteType] = {}

    def get_graphql_type_field(self, field: FIELD_ARGUMENT_TYPE) -> GraphQLType:
        # TODO: Completely replace with get_graphql_type

        optional = _is_optional(field)

        if _is_list(field):
            graphql_type = self.from_list(field)
        elif _is_union(field):
            graphql_type = self.from_union(field.type)
        else:
            graphql_type = self.get_graphql_type(field.type)

        # TODO: Abstract this somehow. Logic is tricky
        return GraphQLNonNull(graphql_type) if not optional else graphql_type

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

        return GraphQLArgument(
            type_=argument_type,
            default_value=default_value,
            description=argument.description
        )

    def from_enum(self, enum: FIELD_ARGUMENT_TYPE) -> GraphQLEnumType:
        return GraphQLEnumType(
            name=enum.name,
            values={
                item.name: self.from_enum_value(item) for item in enum.values
            },
            description=enum.description
        )

    def from_enum_value(self, enum_value: FIELD_ARGUMENT_TYPE) -> GraphQLEnumValue:
        return GraphQLEnumValue(enum_value.value)

    def from_directive(self, directive: DirectiveDefinition) -> GraphQLDirective:
        arguments = get_arguments_for_directive(directive.resolver)
        graphql_arguments = {
            argument.name: self.from_argument(argument)
            for argument in arguments
        }

        return GraphQLDirective(
            name=directive.name,
            locations=directive.locations,
            args=graphql_arguments,
            description=directive.description
        )

    def from_field(self, field: FIELD_ARGUMENT_TYPE) -> GraphQLField:

        # This shouldn't be used here. Messes up conversion hierarchy
        field_type = self.get_graphql_type_field(field)

        resolver = self.from_resolver(field)
        subscribe = None

        if field.is_subscription:
            subscribe = resolver
            resolver = lambda event, *_, **__: event

        return GraphQLField(
            type_=field_type,
            args={
                argument.name: self.from_argument(argument)
                for argument in field.arguments
            },
            resolve=resolver,
            subscribe=subscribe,
            deprecation_reason=field.deprecation_reason
        )

    def from_input_field(self, field: FIELD_ARGUMENT_TYPE) -> GraphQLInputField:
        if field.default_value in [undefined, UNSET]:
            default_value = Undefined
        else:
            default_value = field.default_value

        field_type = self.get_graphql_type_field(field)

        return GraphQLInputField(
            type_=field_type,
            default_value=default_value,
            description=field.description
        )

    def from_input_object_type(
            self, object_type: FIELD_ARGUMENT_TYPE
    ) -> GraphQLInputObjectType:
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
        return GraphQLInterfaceType(
            name=interface.name,
            # TODO: Does this need to be deferred?
            fields={
                field.name: self.from_field(field)
                for field in interface.fields
            },
            interfaces=list(map(self.from_interface, interface.interfaces)),
            description=interface.description,
        )

    def from_list(self, list_: FIELD_ARGUMENT_TYPE) -> GraphQLList:
        of_type = self.get_graphql_type_field(list_.child)
        return GraphQLList(of_type)

    def from_object_type(self, object_type: Type) -> GraphQLObjectType:
        # TODO: Use StrawberryObjectType when it's implemented in another PR
        if not hasattr(object_type, "_type_definition"):
            raise TypeError(f"Wrong type passed to get object type {object_type}")

        type_definition = object_type._type_definition

        object_type = GraphQLObjectType(
            name=type_definition.name,
            # TODO: Does this need to be deferred?
            fields={
                field.name: self.from_field(field)
                for field in type_definition.fields
            },
            interfaces=list(map(self.from_interface, type_definition.interfaces)),
            is_type_of=lambda obj, _: isinstance(obj, type_definition.origin),
            description=type_definition.description,
        )

        self.type_map[type_definition.name] = ConcreteType(
            definition=type_definition, implementation=object_type
        )

        return object_type

    def from_non_optional(self, optional: FIELD_ARGUMENT_TYPE) -> GraphQLNullableType:
        graphql_type = self.get_graphql_type(optional.type)
        return GraphQLNullableType(graphql_type)

    def from_resolver(self, field: FIELD_ARGUMENT_TYPE) -> Callable:
        # TODO: Take in StrawberryResolver
        return get_resolver(field)

    def from_scalar(self, scalar: Type) -> GraphQLScalarType:
        return get_scalar_type(scalar, self.type_map)

    def from_union(self, union: StrawberryUnion, type_map: TypeMap) -> GraphQLUnionType:
        return get_union_type(union, type_map)


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
