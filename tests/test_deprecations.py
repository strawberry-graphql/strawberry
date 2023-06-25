import pytest

import strawberry
from strawberry.utils.deprecations import DEPRECATION_MESSAGES


@strawberry.type
class A:
    a: int


def test_type_definition_is_aliased():
    assert A.__strawberry_definition__ is A._type_definition


def test_get_warns():
    with pytest.warns(match=DEPRECATION_MESSAGES._TYPE_DEFINITION):
        assert A._type_definition.fields[0]


def test_can_import_type_definition():
    from strawberry.types.types import TypeDefinition

    assert TypeDefinition
