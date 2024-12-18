import re
from typing_extensions import Literal

import pydantic
import pytest
from pydantic import BaseModel, ValidationError, conlist

import strawberry
from strawberry.experimental.pydantic._compat import IS_PYDANTIC_V1
from strawberry.types.base import StrawberryObjectDefinition, StrawberryOptional
from tests.experimental.pydantic.utils import needs_pydantic_v1, needs_pydantic_v2


@pytest.mark.parametrize(
    ("pydantic_type", "field_type"),
    [
        (pydantic.ConstrainedInt, int),
        (pydantic.PositiveInt, int),
        (pydantic.NegativeInt, int),
        (pydantic.StrictInt, int),
        (pydantic.StrictStr, str),
        (pydantic.ConstrainedStr, str),
        (pydantic.SecretStr, str),
        (pydantic.StrictBool, bool),
        (pydantic.ConstrainedBytes, bytes),
        (pydantic.SecretBytes, bytes),
        (pydantic.EmailStr, str),
        (pydantic.AnyUrl, str),
        (pydantic.AnyHttpUrl, str),
        (pydantic.HttpUrl, str),
        (pydantic.PostgresDsn, str),
        (pydantic.RedisDsn, str),
    ]
    if IS_PYDANTIC_V1
    else [
        (pydantic.PositiveInt, int),
        (pydantic.NegativeInt, int),
        (pydantic.StrictInt, int),
        (pydantic.StrictStr, str),
        (pydantic.SecretStr, str),
        (pydantic.StrictBool, bool),
        (pydantic.SecretBytes, bytes),
        (pydantic.EmailStr, str),
        (pydantic.AnyUrl, str),
        (pydantic.AnyHttpUrl, str),
        (pydantic.HttpUrl, str),
        (pydantic.PostgresDsn, str),
        (pydantic.RedisDsn, str),
    ],
)
def test_types(pydantic_type, field_type):
    class Model(pydantic.BaseModel):
        field: pydantic_type

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: StrawberryObjectDefinition = Type.__strawberry_definition__
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert field.type is field_type


@needs_pydantic_v1
@pytest.mark.parametrize(
    ("pydantic_type", "field_type"),
    [(pydantic.NoneStr, str)] if IS_PYDANTIC_V1 else [],
)
def test_types_optional(pydantic_type, field_type):
    class Model(pydantic.BaseModel):
        field: pydantic_type

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: StrawberryObjectDefinition = Type.__strawberry_definition__
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert isinstance(field.type, StrawberryOptional)
    assert field.type.of_type is field_type


@needs_pydantic_v2
def test_conint():
    class Model(pydantic.BaseModel):
        field: pydantic.conint(lt=100)

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: StrawberryObjectDefinition = Type.__strawberry_definition__
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert field.type is int


@needs_pydantic_v1
def test_confloat():
    class Model(pydantic.BaseModel):
        field: pydantic.confloat(lt=100.5)

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: StrawberryObjectDefinition = Type.__strawberry_definition__
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert field.type is float


@needs_pydantic_v1
def test_constr():
    class Model(pydantic.BaseModel):
        field: pydantic.constr(max_length=100)

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: StrawberryObjectDefinition = Type.__strawberry_definition__
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert field.type is str


@needs_pydantic_v1
def test_constrained_list():
    class User(BaseModel):
        friends: conlist(str, min_items=1)

    @strawberry.experimental.pydantic.type(model=User, all_fields=True)
    class UserType: ...

    assert UserType.__strawberry_definition__.fields[0].name == "friends"
    assert (
        UserType.__strawberry_definition__.fields[0].type_annotation.raw_annotation
        == list[str]
    )

    data = UserType(friends=[])

    with pytest.raises(
        ValidationError,
        match=re.escape(
            "ensure this value has at least 1 items "
            "(type=value_error.list.min_items; limit_value=1)",
        ),
    ):
        # validation errors should happen when converting to pydantic
        data.to_pydantic()


@needs_pydantic_v1
def test_constrained_list_nested():
    class User(BaseModel):
        friends: conlist(conlist(int, min_items=1), min_items=1)

    @strawberry.experimental.pydantic.type(model=User, all_fields=True)
    class UserType: ...

    assert UserType.__strawberry_definition__.fields[0].name == "friends"
    assert (
        UserType.__strawberry_definition__.fields[0].type_annotation.raw_annotation
        == list[list[int]]
    )


@needs_pydantic_v1
@pytest.mark.parametrize(
    "pydantic_type",
    [
        pydantic.StrBytes,
        pydantic.NoneStrBytes,
        pydantic.PyObject,
        pydantic.FilePath,
        pydantic.DirectoryPath,
        pydantic.Json,
        pydantic.PaymentCardNumber,
        pydantic.ByteSize,
        # pydantic.JsonWrapper,
    ]
    if IS_PYDANTIC_V1
    else [],
)
def test_unsupported_types(pydantic_type):
    class Model(pydantic.BaseModel):
        field: pydantic_type

    with pytest.raises(
        strawberry.experimental.pydantic.exceptions.UnsupportedTypeError
    ):

        @strawberry.experimental.pydantic.type(Model)
        class Type:
            field: strawberry.auto


def test_literal_types():
    class Model(pydantic.BaseModel):
        field: Literal["field"]

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: StrawberryObjectDefinition = Type.__strawberry_definition__
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert field.type == Literal["field"]
