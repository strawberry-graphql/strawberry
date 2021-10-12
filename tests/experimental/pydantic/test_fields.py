import pytest

import pydantic

import strawberry
from strawberry.type import StrawberryOptional
from strawberry.types.types import TypeDefinition


@pytest.mark.parametrize(
    "pydantic_type, field_type",
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
    ],
)
def test_types(pydantic_type, field_type):
    class Model(pydantic.BaseModel):
        field: pydantic_type

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: TypeDefinition = Type._type_definition
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert field.type is field_type


@pytest.mark.parametrize(
    "pydantic_type, field_type",
    [(pydantic.NoneStr, str)],
)
def test_types_optional(pydantic_type, field_type):
    class Model(pydantic.BaseModel):
        field: pydantic_type

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: TypeDefinition = Type._type_definition
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert isinstance(field.type, StrawberryOptional)
    assert field.type.of_type is field_type


def test_conint():
    class Model(pydantic.BaseModel):
        field: pydantic.conint(lt=100)

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: TypeDefinition = Type._type_definition
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert field.type is int


def test_constr():
    class Model(pydantic.BaseModel):
        field: pydantic.constr(max_length=100)

    @strawberry.experimental.pydantic.type(Model)
    class Type:
        field: strawberry.auto

    definition: TypeDefinition = Type._type_definition
    assert definition.name == "Type"

    [field] = definition.fields

    assert field.python_name == "field"
    assert field.type is str


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
        # pydantic.ConstrainedList,
        # pydantic.ConstrainedSet,
        # pydantic.JsonWrapper,
    ],
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
