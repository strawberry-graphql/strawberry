from typing import Optional

import strawberry
from strawberry.extensions.max_aliases import MaxAliasesLimiter


@strawberry.type
class Human:
    name: str
    email: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self, name: Optional[str] = None, email: Optional[str] = None) -> Human:
        return Human(name="Jane Doe", email="jane@example.com")

    version: str
    user1: Human
    user2: Human
    user3: Human


def test_2_aliases_same_content():
    query = """
    {
      matt: user(name: "matt") {
        email
      }
      matt_alias: user(name: "matt") {
        email
      }
    }
    """

    result = _execute_with_max_aliases(query, 1)

    assert len(result.errors) == 1
    assert result.errors[0].message == "2 aliases found. Allowed: 1"


def test_2_aliases_different_content():
    query = """
    query read {
      matt: user(name: "matt") {
        email
      }
      matt_alias: user(name: "matt42") {
        email
      }
    }
    """

    result = _execute_with_max_aliases(query, 1)

    assert len(result.errors) == 1
    assert result.errors[0].message == "2 aliases found. Allowed: 1"


def test_multiple_aliases_some_overlap_in_content():
    query = """
    query read {
      matt: user(name: "matt") {
        email
      }
      jane: user(name: "jane") {
        email
      }
      matt_alias: user(name: "matt") {
        email
      }
    }
    """

    result = _execute_with_max_aliases(query, 1)

    assert len(result.errors) == 1
    assert result.errors[0].message == "3 aliases found. Allowed: 1"


def test_multiple_arguments():
    query = """
    query read {
      matt: user(name: "matt", email: "matt@example.com") {
        email
      }
      jane: user(name: "jane") {
        email
      }
      matt_alias: user(name: "matt", email: "matt@example.com") {
        email
      }
    }
    """

    result = _execute_with_max_aliases(query, 1)

    assert len(result.errors) == 1
    assert result.errors[0].message == "3 aliases found. Allowed: 1"


def test_alias_in_nested_field():
    query = """
    query read {
      matt: user(name: "matt") {
        email_address: email
      }
    }
    """

    result = _execute_with_max_aliases(query, 1)

    assert len(result.errors) == 1
    assert result.errors[0].message == "2 aliases found. Allowed: 1"


def test_alias_in_fragment():
    query = """
    fragment humanInfo on Human {
      email_address: email
    }
    query read {
      matt: user(name: "matt") {
        ...humanInfo
      }
    }
    """

    result = _execute_with_max_aliases(query, 1)

    assert len(result.errors) == 1
    assert result.errors[0].message == "2 aliases found. Allowed: 1"


def test_2_top_level_1_nested():
    query = """{
      matt: user(name: "matt") {
        email_address: email
      }
      matt_alias: user(name: "matt") {
        email
      }
    }
    """
    result = _execute_with_max_aliases(query, 2)

    assert len(result.errors) == 1
    assert result.errors[0].message == "3 aliases found. Allowed: 2"


def test_no_error_one_aliased_one_without():
    query = """
    {
      user(name: "matt") {
        email
      }
      matt_alias: user(name: "matt") {
        email
      }
    }
    """

    result = _execute_with_max_aliases(query, 1)

    assert not result.errors


def test_no_error_for_multiple_but_not_too_many_aliases():
    query = """{
      matt: user(name: "matt") {
        email
      }
      matt_alias: user(name: "matt") {
        email
      }
    }
    """

    result = _execute_with_max_aliases(query, 2)

    assert not result.errors


def _execute_with_max_aliases(query: str, max_alias_count: int):
    schema = strawberry.Schema(
        Query, extensions=[MaxAliasesLimiter(max_alias_count=max_alias_count)]
    )

    return schema.execute_sync(query)
