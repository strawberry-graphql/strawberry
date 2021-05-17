from typing import Optional, Union

import strawberry
from strawberry.arguments import UNSET


def test_default_unset():
    @strawberry.input
    class User:
        name: Union[Optional[str], UNSET]

    assert User().name is UNSET

    definition = User._type_definition
    assert len(definition.fields) == 1

    assert definition.fields[0].graphql_name == "name"
    field_definition = definition.fields[0]

    assert field_definition.type is str
    assert field_definition.is_optional is True
    assert field_definition.default_value is UNSET
