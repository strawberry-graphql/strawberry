import sys
import textwrap
from enum import Enum
from typing import List, Optional, Union

import pydantic
import pytest

import strawberry
from tests.experimental.pydantic.utils import needs_pydantic_v1

from strawberry.experimental.pydantic.object_type import register_first_class


def test_basic_type_field_list():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    register_first_class(User)

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(age=1, password="ABC")

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Query {
      user: User!
    }

    type User {
      age: Int!
      password: String
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1
