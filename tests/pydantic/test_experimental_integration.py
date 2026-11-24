"""`strawberry.pydantic` and `strawberry.experimental.pydantic` can't be mixed."""

import textwrap

import pydantic
import pytest

import strawberry
from strawberry.experimental.pydantic import UnregisteredTypeException
from strawberry.pydantic.exceptions import UnregisteredPydanticTypeError


def test_experimental_types_cannot_use_strawberry_pydantic_models():
    @strawberry.pydantic.type
    class Address(pydantic.BaseModel):
        city: str

    class UserModel(pydantic.BaseModel):
        address: Address

    with pytest.raises(
        UnregisteredTypeException,
        match=(
            r"^Address is decorated with `strawberry.pydantic`, which can't be mixed "
            r"with `strawberry.experimental.pydantic`: move the models that use it "
            r"to `strawberry.pydantic` too$"
        ),
    ):

        @strawberry.experimental.pydantic.type(model=UserModel, all_fields=True)
        class User:
            pass


@pytest.mark.raises_strawberry_exception(
    UnregisteredPydanticTypeError,
    match=(
        r"^`User.address` uses `AddressModel`, which only has a "
        r"`strawberry.experimental.pydantic` type: decorate it with "
        r"`@strawberry.pydantic.type`$"
    ),
)
def test_strawberry_pydantic_models_cannot_use_experimental_types():
    class AddressModel(pydantic.BaseModel):
        city: str

    @strawberry.experimental.pydantic.type(model=AddressModel, all_fields=True)
    class Address:
        pass

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        address: AddressModel

    strawberry.Schema(query=User)


def test_experimental_types_missing_the_input_of_a_model_with_both_types():
    class AddressModel(pydantic.BaseModel):
        city: str

    @strawberry.experimental.pydantic.type(model=AddressModel, all_fields=True)
    class Address:
        pass

    strawberry.pydantic.type(AddressModel, name="NewAddress")

    class UserModel(pydantic.BaseModel):
        address: AddressModel

    with pytest.raises(
        UnregisteredTypeException, match="did you forget to register it\\?"
    ):

        @strawberry.experimental.pydantic.input(model=UserModel, all_fields=True)
        class UserInput:
            pass


@pytest.mark.raises_strawberry_exception(
    UnregisteredPydanticTypeError,
    match=(
        r"^`User.address` uses `AddressSubclass`, which isn't a Strawberry type: "
        r"decorate it with `@strawberry.pydantic.type`$"
    ),
)
def test_subclasses_of_models_with_experimental_types():
    class AddressModel(pydantic.BaseModel):
        city: str

    @strawberry.experimental.pydantic.type(model=AddressModel, all_fields=True)
    class Address:
        pass

    class AddressSubclass(AddressModel):
        pass

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        address: AddressSubclass

    strawberry.Schema(query=User)


def test_models_can_have_both_types_while_migrating():
    class AddressModel(pydantic.BaseModel):
        city: str

    @strawberry.experimental.pydantic.type(model=AddressModel, all_fields=True)
    class Address:
        pass

    strawberry.pydantic.type(AddressModel, name="NewAddress")

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        address: AddressModel

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(address=AddressModel(city="Rome"))

        @strawberry.field
        def address(self) -> Address:
            return Address.from_pydantic(AddressModel(city="Turin"))

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Address {
      city: String!
    }

    type NewAddress {
      city: String!
    }

    type Query {
      user: User!
      address: Address!
    }

    type User {
      address: NewAddress!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync("{ user { address { city } } address { city } }")

    assert not result.errors
    assert result.data == {
        "user": {"address": {"city": "Rome"}},
        "address": {"city": "Turin"},
    }
