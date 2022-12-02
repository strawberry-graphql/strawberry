import dataclasses

import strawberry
from strawberry.tools import PartialType
from strawberry.type import StrawberryOptional


def test_partialtype():
    @strawberry.type
    class RoleRead:
        name: str
        description: str

    @strawberry.type
    class UserRead:
        firstname: str
        lastname: str
        role: RoleRead

    @strawberry.input
    class RoleInput(RoleRead):
        pass

    @strawberry.input
    class UserQuery(UserRead, metaclass=PartialType):
        role: RoleInput

    read_firstname, read_lastname, read_role = UserRead._type_definition.fields

    # user read type firstname field tests
    assert read_firstname.python_name == "firstname"
    assert read_firstname.graphql_name is None
    assert read_firstname.default is dataclasses.MISSING
    assert read_firstname.type is str

    # user read type lastname field tests
    assert read_lastname.python_name == "lastname"
    assert read_lastname.graphql_name is None
    assert read_lastname.default is dataclasses.MISSING
    assert read_lastname.type is str

    assert read_role.python_name == "role"
    assert read_role.graphql_name is None
    assert read_role.default is dataclasses.MISSING
    assert read_role.type is RoleRead

    query_firstname, query_lastname, query_role = UserQuery._type_definition.fields

    # user query type firstname field tests
    assert query_firstname.python_name == "firstname"
    assert query_firstname.graphql_name is None
    assert query_firstname.default is strawberry.UNSET
    assert isinstance(query_firstname.type, StrawberryOptional)
    assert query_firstname.type.of_type is str

    # user query type lastname field tests
    assert query_lastname.python_name == "lastname"
    assert query_lastname.graphql_name is None
    assert query_lastname.default is strawberry.UNSET
    assert isinstance(query_lastname.type, StrawberryOptional)
    assert query_lastname.type.of_type is str

    # user query type role field tests
    assert query_role.python_name == "role"
    assert query_role.graphql_name is None
    assert query_role.default is strawberry.UNSET
    assert isinstance(query_role.type, StrawberryOptional)
    assert query_role.type.of_type is RoleInput
