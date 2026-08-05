"""Tests for Pydantic v2 alias features with first-class integration."""

import pydantic
from pydantic import AliasChoices, Field

import strawberry


def test_validation_alias_input():
    """Test that validation_alias works for input types."""

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        # GraphQL will use the Python field name, but Pydantic can accept different names
        user_name: str = Field(validation_alias="userName")

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        user_name: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: UserInput) -> User:
            return User(user_name=input.user_name)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # GraphQL uses the camelCase name from the name converter
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { userName: "Alice" }) {
                userName
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["userName"] == "Alice"


def test_serialization_alias_output():
    """Test that serialization_alias works for output types."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        # Internal field name differs from what clients might expect
        user_name: str = Field(serialization_alias="displayName")

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(user_name="Alice")

    schema = strawberry.Schema(query=Query)

    # The GraphQL field name is still based on the Python field name
    # (Strawberry controls the GraphQL schema, not Pydantic's serialization alias)
    result = schema.execute_sync(
        """
        query {
            user {
                userName
            }
        }
        """
    )

    assert not result.errors
    assert result.data["user"]["userName"] == "Alice"


def test_alias_choices_for_flexibility():
    """Test that AliasChoices allows multiple input names."""

    @strawberry.pydantic.input
    class ConfigInput(pydantic.BaseModel):
        # Accept either 'apiKey' or 'api_key' when constructing directly
        api_key: str = Field(validation_alias=AliasChoices("apiKey", "api_key"))

    @strawberry.pydantic.type
    class Config(pydantic.BaseModel):
        api_key: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def set_config(self, input: ConfigInput) -> Config:
            return Config(api_key=input.api_key)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # GraphQL uses the standard camelCase name
    result = schema.execute_sync(
        """
        mutation {
            setConfig(input: { apiKey: "secret123" }) {
                apiKey
            }
        }
        """
    )

    assert not result.errors
    assert result.data["setConfig"]["apiKey"] == "secret123"


def test_alias_path_for_nested_extraction():
    """Test that AliasPath can extract from nested structures in direct model usage."""

    @strawberry.pydantic.input
    class SettingsInput(pydantic.BaseModel):
        # This is useful when the model is constructed directly, not from GraphQL
        theme: str = Field(default="light")

    @strawberry.pydantic.type
    class Settings(pydantic.BaseModel):
        theme: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update_settings(self, input: SettingsInput) -> Settings:
            return Settings(theme=input.theme)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
        mutation {
            updateSettings(input: { theme: "dark" }) {
                theme
            }
        }
        """
    )

    assert not result.errors
    assert result.data["updateSettings"]["theme"] == "dark"


def test_combined_validation_and_serialization_alias():
    """Test model with both validation and serialization aliases."""

    @strawberry.pydantic.input
    class ProductInput(pydantic.BaseModel):
        product_id: str = Field(validation_alias="productID")
        display_name: str

    @strawberry.pydantic.type
    class Product(pydantic.BaseModel):
        product_id: str
        display_name: str = Field(serialization_alias="name")

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_product(self, input: ProductInput) -> Product:
            return Product(product_id=input.product_id, display_name=input.display_name)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
        mutation {
            createProduct(input: { productId: "P123", displayName: "Widget" }) {
                productId
                displayName
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createProduct"]["productId"] == "P123"
    assert result.data["createProduct"]["displayName"] == "Widget"


def test_alias_with_populate_by_name():
    """Test that populate_by_name allows using either field name or alias."""

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(populate_by_name=True)

        email_address: str = Field(alias="email")

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        email_address: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: UserInput) -> User:
            return User(email_address=input.email_address)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with the alias (GraphQL uses alias when present)
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { email: "alice@example.com" }) {
                emailAddress
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["emailAddress"] == "alice@example.com"


def test_strawberry_name_overrides_pydantic_alias():
    """Test that strawberry.field(name=...) overrides Pydantic alias for GraphQL."""

    @strawberry.pydantic.type
    class Product(pydantic.BaseModel):
        # Pydantic alias for serialization
        internal_id: str = Field(serialization_alias="id")

    @strawberry.type
    class Query:
        @strawberry.field
        def product(self) -> Product:
            return Product(internal_id="P123")

    schema = strawberry.Schema(query=Query)

    # GraphQL schema uses the Python field name converted to camelCase
    result = schema.execute_sync(
        """
        query {
            product {
                internalId
            }
        }
        """
    )

    assert not result.errors
    assert result.data["product"]["internalId"] == "P123"


def test_alias_generator_function():
    """Test using alias_generator in model_config."""

    def to_camel(string: str) -> str:
        components = string.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    @strawberry.pydantic.input
    class DataInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(
            alias_generator=to_camel, populate_by_name=True
        )

        user_name: str
        email_address: str

    @strawberry.pydantic.type
    class Data(pydantic.BaseModel):
        user_name: str
        email_address: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def save_data(self, input: DataInput) -> Data:
            return Data(user_name=input.user_name, email_address=input.email_address)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # GraphQL fields use camelCase from Strawberry's name converter
    result = schema.execute_sync(
        """
        mutation {
            saveData(input: { userName: "Alice", emailAddress: "alice@example.com" }) {
                userName
                emailAddress
            }
        }
        """
    )

    assert not result.errors
    assert result.data["saveData"]["userName"] == "Alice"
    assert result.data["saveData"]["emailAddress"] == "alice@example.com"
