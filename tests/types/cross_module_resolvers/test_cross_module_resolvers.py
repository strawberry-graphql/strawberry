"""The following tests ensure that the types are resolved using the correct
module. Concrete types should be non-problematic and are only included
here for completeness. A problematic case is when a type is a string
(forward reference) and can only be resolved at schema construction.
"""

import strawberry

from . import a_mod, b_mod, c_mod, x_mod


def test_a():
    @strawberry.type
    class Query:
        a_list: list[a_mod.AObject]

    [field] = Query.__strawberry_definition__.fields
    assert field.type == list[a_mod.AObject]


def test_a_resolver():
    @strawberry.type
    class Query:
        a_list: list[a_mod.AObject] = strawberry.field(resolver=a_mod.a_resolver)

    [field] = Query.__strawberry_definition__.fields
    assert field.type == list[a_mod.AObject]


def test_a_only_resolver():
    @strawberry.type
    class Query:
        a_list = strawberry.field(resolver=a_mod.a_resolver)

    [field] = Query.__strawberry_definition__.fields
    assert field.type == list[a_mod.AObject]


def test_a_typeless_resolver():
    @strawberry.type
    class Query:
        a_list: list[a_mod.AObject] = strawberry.field(resolver=x_mod.typeless_resolver)

    [field] = Query.__strawberry_definition__.fields
    assert field.type == list[a_mod.AObject]


def test_c_composition_by_name():
    [
        a_field,
        b_field,
        a_method,
        b_method,
    ] = c_mod.CCompositionByName.__strawberry_definition__.fields
    assert a_field.type == list[a_mod.AObject]
    assert b_field.type == list[b_mod.BObject]
    assert a_method.type == list[a_mod.AObject]
    assert b_method.type == list[b_mod.BObject]


def test_c_inheritance():
    [
        a_name,
        a_age,
        a_is_of_full_age,
        b_name,
        b_age,
        b_is_of_full_age,
    ] = c_mod.CInheritance.__strawberry_definition__.fields
    assert a_name.origin == a_mod.ABase
    assert a_age.origin == a_mod.AObject
    assert a_is_of_full_age.origin == a_mod.AObject
    assert b_name.origin == b_mod.BBase
    assert b_age.origin == b_mod.BObject
    assert b_is_of_full_age.origin == b_mod.BObject


def test_c_inheritance_resolver():
    @strawberry.type
    class Query:
        c: list[c_mod.CInheritance] = strawberry.field(
            resolver=c_mod.c_inheritance_resolver
        )

    [field] = Query.__strawberry_definition__.fields
    assert field.type == list[c_mod.CInheritance]


def test_c_inheritance_typeless_resolver():
    @strawberry.type
    class Query:
        c: list[c_mod.CInheritance] = strawberry.field(resolver=x_mod.typeless_resolver)

    [field] = Query.__strawberry_definition__.fields
    assert field.type == list[c_mod.CInheritance]


def test_c_inheritance_resolver_only():
    @strawberry.type
    class Query:
        c = strawberry.field(resolver=c_mod.c_inheritance_resolver)

    [field] = Query.__strawberry_definition__.fields
    assert field.type == list[c_mod.CInheritance]


def test_c_composition_resolver():
    @strawberry.type
    class Query:
        c: list[c_mod.CComposition] = strawberry.field(
            resolver=c_mod.c_composition_resolver
        )

    [field] = Query.__strawberry_definition__.fields
    assert field.type == list[c_mod.CComposition]
    [a_field, b_field] = field.type.of_type.__strawberry_definition__.fields
    assert a_field.type == list[a_mod.AObject]
    assert b_field.type == list[b_mod.BObject]


def test_c_composition_by_name_with_resolvers():
    [
        a_field,
        b_field,
    ] = c_mod.CCompositionByNameWithResolvers.__strawberry_definition__.fields
    assert a_field.type == list[a_mod.AObject]
    assert b_field.type == list[b_mod.BObject]


def test_c_composition_by_name_with_typeless_resolvers():
    [
        a_field,
        b_field,
    ] = c_mod.CCompositionByNameWithTypelessResolvers.__strawberry_definition__.fields
    assert a_field.type == list[a_mod.AObject]
    assert b_field.type == list[b_mod.BObject]


def test_c_composition_only_resolvers():
    [
        a_field,
        b_field,
    ] = c_mod.CCompositionOnlyResolvers.__strawberry_definition__.fields
    assert a_field.type == list[a_mod.AObject]
    assert b_field.type == list[b_mod.BObject]


def test_x_resolver():
    @strawberry.type
    class Query:
        c: list[a_mod.AObject] = strawberry.field(resolver=x_mod.typeless_resolver)

    [c_field] = Query.__strawberry_definition__.fields
    assert c_field.type == list[a_mod.AObject]
