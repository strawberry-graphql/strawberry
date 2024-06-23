"""Strawberry is a Python library for GraphQL.

Strawberry is a Python library for GraphQL that aims to stay close to the GraphQL
specification and allow for a more natural way of defining GraphQL schemas.
"""

from . import experimental, federation, relay
from .arguments import argument
from .custom_scalar import scalar
from .directive import directive, directive_field
from .field import field
from .lazy_type import LazyType, lazy
from .mutation import mutation, subscription
from .object_type import asdict, input, interface, type
from .parent import Parent
from .permission import BasePermission
from .scalars import ID
from .schema import Schema
from .schema_directive import schema_directive
from .types.auto import auto
from .types.enum import enum, enum_value
from .types.info import Info
from .types.private import Private
from .types.union import union
from .unset import UNSET

__all__ = [
    "BasePermission",
    "experimental",
    "ID",
    "Info",
    "UNSET",
    "lazy",
    "LazyType",
    "Parent",
    "Private",
    "Schema",
    "argument",
    "directive",
    "directive_field",
    "schema_directive",
    "enum",
    "enum_value",
    "federation",
    "field",
    "input",
    "interface",
    "mutation",
    "scalar",
    "subscription",
    "type",
    "union",
    "auto",
    "asdict",
    "relay",
]
