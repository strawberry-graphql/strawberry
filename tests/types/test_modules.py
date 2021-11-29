# The following tests ensure that the resolver is able to resolve all types
# using the correct module. Concrete types should be non-problematic and are
# only included here for completeless. The problematic cases are where a
# `str` is given as type which can only be resolved at schema construction.
#
# Important: For this tests not to hide any wrong resolves no types must
# be imported into the namespaces under the same name and all type names
# must be unique. e.g. when importing `a.AObject` into the `c` module it
# must be renamed to something like `C_AObject`. That way wrong resolves
# like `C_AObject` being loaded from `a` or `AObject` being loaded from
# `c` can be detected.


from typing import List

from modules import a_mod, b_mod, c_mod, x_mod

import strawberry


def test_a():
    @strawberry.type
    class Query:
        a_list: List[a_mod.AObject]

    [field] = Query._type_definition.fields
    assert field.type == List[a_mod.AObject]


def test_a_resolver():
    @strawberry.type
    class Query:
        a_list: List[a_mod.AObject] = strawberry.field(resolver=a_mod.a_resolver)

    [field] = Query._type_definition.fields
    assert field.type == List[a_mod.AObject]


def test_a_only_resolver():
    @strawberry.type
    class Query:
        a_list = strawberry.field(resolver=a_mod.a_resolver)

    [field] = Query._type_definition.fields
    assert field.type == List[a_mod.AObject]


def test_a_typeless_resolver():
    @strawberry.type
    class Query:
        a_list: List[a_mod.AObject] = strawberry.field(resolver=x_mod.typeless_resolver)

    [field] = Query._type_definition.fields
    assert field.type == List[a_mod.AObject]


def test_c_composition_by_name():
    [a_field, b_field] = c_mod.CObjectCompositionByName._type_definition.fields
    assert a_field.type == List[a_mod.AObject]
    assert b_field.type == List[b_mod.BObject]


def test_c_inheritance():
    [a_name, a_age, b_name, b_age] = c_mod.CInheritance._type_definition.fields
    assert a_name.origin == a_mod.ABase
    assert a_age.origin == a_mod.AObject
    assert b_name.origin == b_mod.BBase
    assert b_age.origin == b_mod.BObject


def test_c_inheritance_resolver():
    @strawberry.type
    class Query:
        c: List[c_mod.CInheritance] = strawberry.field(
            resolver=c_mod.c_inheritance_resolver
        )

    [field] = Query._type_definition.fields
    assert field.type == List[c_mod.CInheritance]


def test_c_inheritance_typeless_resolver():
    @strawberry.type
    class Query:
        c: List[c_mod.CInheritance] = strawberry.field(resolver=x_mod.typeless_resolver)

    [field] = Query._type_definition.fields
    assert field.type == List[c_mod.CInheritance]


def test_c_inheritance_resolver_only():
    @strawberry.type
    class Query:
        c = strawberry.field(resolver=c_mod.c_inheritance_resolver)

    [field] = Query._type_definition.fields
    assert field.type == List[c_mod.CInheritance]


def test_c_composition_resolver():
    @strawberry.type
    class Query:
        c: c_mod.CComposition = strawberry.field(resolver=c_mod.c_composition_resolver)

    [field] = Query._type_definition.fields
    assert field.type == List[c_mod.CComposition]
    [a_field, b_field] = field.type.of_type._type_definition.fields
    assert a_field.type == List[a_mod.AObject]
    assert b_field.type == List[b_mod.BObject]


def test_c_composition_by_name_resolver():
    @strawberry.type
    class Query:
        c: List[c_mod.CCompositionByName] = strawberry.field(
            resolver=c_mod.c_composition_by_name_resolver
        )

    [field] = Query._type_definition.fields
    assert field.type == List[c_mod.CCompositionByName]
    [a_field, b_field] = field.type.of_type._type_definition.fields
    assert a_field.type == List[a_mod.AObject]
    assert b_field.type == List[b_mod.BObject]


def test_c_composition_by_name():
    [a_field, b_field] = c_mod.CCompositionByName._type_definition.fields
    assert a_field.type == List[a_mod.AObject]
    assert b_field.type == List[b_mod.BObject]


def test_c_composition_by_name_with_resolvers():
    [a_field, b_field] = c_mod.CCompositionByNameWithResolvers._type_definition.fields
    assert a_field.type == List[a_mod.AObject]
    assert b_field.type == List[b_mod.BObject]


def test_c_composition_by_name_with_typeless_resolvers():
    [
        a_field,
        b_field,
    ] = c_mod.CCompositionByNameWithTypelessResolvers._type_definition.fields
    assert a_field.type == List[a_mod.AObject]
    assert b_field.type == List[b_mod.BObject]


def test_c_composition_only_resolvers():
    [a_field, b_field] = c_mod.CCompositionOnlyResolvers._type_definition.fields
    assert a_field.type == List[a_mod.AObject]
    assert b_field.type == List[b_mod.BObject]


def test_x_resolver():
    @strawberry.type
    class Query:
        c: List[a_mod.AObject] = strawberry.field(resolver=x_mod.typeless_resolver)

    [c_field] = Query._type_definition.fields
    assert c_field.type == List[a_mod.AObject]
