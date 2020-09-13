import dataclasses
import typing
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Type, Union

from graphql import GraphQLArgument, GraphQLField, GraphQLInputField, GraphQLType

from .permission import BasePermission
from .types.types import FederationFieldParams


@dataclass
class StrawberryField:
    name: str
    field_type: Type = typing.cast(Type, dataclasses.MISSING)
    resolver: Optional[Callable] = None
    description: Optional[str] = None
    is_subscription: bool = False
    permission_classes: Optional[List[Type[BasePermission]]] = None
    federation: Optional[FederationFieldParams] = None

    def __call__(self, resolver: Callable):
        self.resolver = resolver

    def to_graphql_field(self) -> Union[GraphQLField, GraphQLInputField]:

        # TODO: Can is_input be determined without the strawberry.type?
        if self.is_input:
            return GraphQLInputField(
                self.graphql_field_type,
                description=self.description,
                default_value=self.default_value,
            )

        if self.is_subscription:
            return GraphQLField(
                self.graphql_field_type,
                description=self.description,
                subscribe=self.resolver,
                resolve=lambda event, *_args, **_kwargs: event,
                args=self.graphql_field_args,
            )

        return GraphQLField(
            self.graphql_field_type,
            description=self.description,
            resolve=self.resolver,
            args=self.graphql_field_args,
        )

    @property
    def graphql_field_type(self) -> GraphQLType:
        ...

    @property
    def graphql_field_args(self) -> Dict[str, GraphQLArgument]:
        ...


# class StrawberryFieldOld(dataclasses.Field):
#     _field_definition: FieldDefinition
#
#     def __init__(self, field_definition: FieldDefinition):
#         self._field_definition = field_definition
#
#         super().__init__(  # type: ignore
#             default=dataclasses.MISSING,
#             default_factory=dataclasses.MISSING,
#             init=field_definition.base_resolver is None,
#             repr=True,
#             hash=None,
#             compare=True,
#             metadata=None,
#         )
#
#     def __call__(self, resolver: Callable) -> Callable:
#         """Migrate the field definition to the resolver"""
#
#         field_definition = self._field_definition
#         # note that field_definition.name is finalized in type_resolver._get_fields
#
#         field_definition.origin_name = resolver.__name__
#         field_definition.origin = resolver
#         field_definition.base_resolver = resolver
#         field_definition.arguments = get_arguments_from_resolver(resolver)
#         field_definition.type = resolver.__annotations__.get("return", None)
#
#         if not inspect.ismethod(resolver):
#             # resolver is a normal function
#             resolver._field_definition = field_definition  # type: ignore
#         else:
#             # resolver is a bound method and immutable (most likely a
#             # classmethod or an instance method). We need to monkeypatch its
#             # underlying .__func__ function
#             # https://stackoverflow.com/a/7891681/8134178
#             resolver.__func__._field_definition = field_definition  # type:ignore
#
#         return resolver
#
#     def __setattr__(self, name, value):
#         if name == "type":
#             self._field_definition.type = value
#
#         if value and name == "name":
#             if not self._field_definition.origin_name:
#                 self._field_definition.origin_name = value
#
#             if not self._field_definition.name:
#                 self._field_definition.name = to_camel_case(value)
#
#         return super().__setattr__(name, value)
#


def field(
    resolver: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    federation: Optional[FederationFieldParams] = None
) -> StrawberryField:
    """Annotates a method or property as a GraphQL field.

    This is normally used inside a type declaration:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = strawberry.field(description="ABC")

    >>>     @strawberry.field(description="ABC")
    >>>     def field_with_resolver(self, info) -> str:
    >>>         return "abc"

    it can be used both as decorator and as a normal function.
    """

    return StrawberryField(
        name=name,
        resolver=resolver,
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes,
        federation=federation,
    )

    # field_definition = FieldDefinition(
    #     origin_name=None,  # modified by resolver in __call__
    #     name=name,  # modified by resolver in __call__
    #     type=None,  # type: ignore
    #     origin=resolver,  # type: ignore
    #     description=description,
    #     base_resolver=resolver,
    #     is_subscription=is_subscription,
    #     permission_classes=permission_classes or [],
    #     arguments=[],  # modified by resolver in __call__
    #     federation=federation or FederationFieldParams(),
    # )
    #
    # field_ = StrawberryFieldOld(field_definition)
    #
    # if resolver:
    #     return field_(resolver)
    # return field_
