from typing import Dict, List, Optional, Tuple, Union

from graphql import (
    GraphQLError,
    parse,
    specified_rules,
    validate,
)

import strawberry
from strawberry.extensions.max_aliases import create_validator


@strawberry.type
class Human:
    name: str
    email: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self, name: Optional[str], email: Optional[str]) -> Human:
        pass

    version: str
    user1: Human
    user2: Human
    user3: Human


schema = strawberry.Schema(Query)


def run_query(
    query: str, max_aliases: int
) -> Tuple[List[GraphQLError], Union[Dict[str, int], None]]:
    document = parse(query)

    result = None

    validation_rule = create_validator(max_aliases)

    errors = validate(
        schema._schema,
        document,
        rules=(*specified_rules, validation_rule),
    )

    return errors, result


def test_2_aliases_same_content():
    query = """
    query read {
      matt: user(name: "matt") {
        email
      }
      matt_alias: user(name: "matt") {
        email
      }
    }
    """

    errors, result = run_query(query, 1)

    assert len(errors) == 1
    assert errors[0].message == "2 aliases found. Allowed: 1"
    assert not result


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

    errors, result = run_query(query, 1)

    assert len(errors) == 1
    assert errors[0].message == "2 aliases found. Allowed: 1"


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

    errors, result = run_query(query, 1)

    assert len(errors) == 1
    assert errors[0].message == "3 aliases found. Allowed: 1"
    assert not result


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

    errors, result = run_query(query, 1)

    assert len(errors) == 1
    assert errors[0].message == "3 aliases found. Allowed: 1"
    assert not result


def test_aliased_argument():
    query = """
    query read {
      matt: user(name: "matt") {
        email_address: email
      }
    }
    """

    errors, result = run_query(query, 1)

    assert len(errors) == 1
    assert errors[0].message == "2 aliases found. Allowed: 1"
    assert not result


def test_aliased_argument_in_fragment():
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

    errors, result = run_query(query, 1)

    assert len(errors) == 1
    assert errors[0].message == "2 aliases found. Allowed: 1"
    assert not result


def test_no_error_one_aliased_one_without():
    query = """
    query read {
      user(name: "matt") {
        email
      }
      matt_alias: user(name: "matt") {
        email
      }
    }
    """

    errors, result = run_query(query, 1)

    assert len(errors) == 0


def test_no_error_for_multiple_but_not_too_many_aliases():
    query = """
    query read {
      matt: user(name: "matt") {
        email
      }
      matt_alias: user(name: "matt") {
        email
      }
    }
    """

    errors, result = run_query(query, 2)

    assert len(errors) == 0
