import textwrap

import pytest

import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types.info import Info


def test_config_post_init_auto_camel_case():
    config = StrawberryConfig(auto_camel_case=True)

    assert config.name_converter.auto_camel_case is True


def test_config_post_init_no_auto_camel_case():
    config = StrawberryConfig(auto_camel_case=False)

    assert config.name_converter.auto_camel_case is False


def test_config_post_init_info_class():
    class CustomInfo(Info):
        test: str = "foo"

    config = StrawberryConfig(info_class=CustomInfo)

    assert config.info_class is CustomInfo
    assert config.info_class.test == "foo"


def test_config_post_init_info_class_is_default():
    config = StrawberryConfig()

    assert config.info_class is Info


def test_config_post_init_info_class_is_not_subclass():
    with pytest.raises(TypeError) as exc_info:
        StrawberryConfig(info_class=object)

    assert str(exc_info.value) == "`info_class` must be a subclass of strawberry.Info"


def test_lexicographic_sort_schema_defaults_to_false():
    assert StrawberryConfig().lexicographic_sort_schema is False


def test_lexicographic_sort_schema_preserves_definition_order_by_default():
    @strawberry.type
    class Query:
        @strawberry.field
        def zebra(self) -> int: ...

        @strawberry.field
        def apple(self) -> int: ...

    schema = strawberry.Schema(query=Query)

    expected = """\
    type Query {
      zebra: Int!
      apple: Int!
    }"""

    assert str(schema) == textwrap.dedent(expected).strip()


def test_lexicographic_sort_schema_sorts_fields_and_types():
    @strawberry.type
    class User:
        name: str
        age: int

    @strawberry.type
    class Query:
        @strawberry.field
        def user_by_name(self, name: str) -> User: ...

        @strawberry.field
        def all_users(self) -> list[User]: ...

        @strawberry.field
        def user_by_id(self, id: int) -> User: ...

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(lexicographic_sort_schema=True),
    )

    expected = """\
    type Query {
      allUsers: [User!]!
      userById(id: Int!): User!
      userByName(name: String!): User!
    }

    type User {
      age: Int!
      name: String!
    }"""

    assert str(schema) == textwrap.dedent(expected).strip()


def test_lexicographic_sort_schema_still_executes():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: str) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(lexicographic_sort_schema=True),
    )

    result = schema.execute_sync('{ hello(name: "Patrick") }')

    assert not result.errors
    assert result.data == {"hello": "Hi Patrick"}
