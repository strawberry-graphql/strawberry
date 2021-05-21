import re
from typing import List, Optional

from graphql import get_introspection_query, parse, specified_rules, validate

import strawberry
from strawberry.validators.depth_limit import depth_limit


@strawberry.interface
class Pet:
    name: str
    owner: "Human"


@strawberry.type
class Cat(Pet):
    pass


@strawberry.type
class Dog(Pet):
    pass


@strawberry.type
class Address:
    street: str
    number: int
    city: str
    country: str


@strawberry.type
class Human:
    name: str
    email: str
    address: Address
    pets: List[Pet]


@strawberry.type
class Query:
    @strawberry.field
    def user(self, name: Optional[str]) -> Human:
        pass

    version: str
    user1: Human
    user2: Human
    user3: Human


schema = strawberry.Schema(Query)


def run_query(query: str, max_depth: int, options=None):
    document = parse(query)

    result = None

    def callback(query_depths):
        nonlocal result
        result = query_depths

    errors = validate(
        schema._schema,
        document,
        rules=(specified_rules + [depth_limit(max_depth, options, callback)]),
    )

    return errors, result


def test_should_count_depth_without_fragment():
    query = """
    query read0 {
      version
    }
    query read1 {
      version
      user {
        name
      }
    }
    query read2 {
      matt: user(name: "matt") {
        email
      }
      andy: user(name: "andy") {
        email
        address {
          city
        }
      }
    }
    query read3 {
      matt: user(name: "matt") {
        email
      }
      andy: user(name: "andy") {
        email
        address {
          city
        }
        pets {
          name
          owner {
            name
          }
        }
      }
    }
    """

    expected = {"read0": 0, "read1": 1, "read2": 2, "read3": 3}

    errors, result = run_query(query, 10)
    assert not errors
    assert result == expected


def test_should_count_with_fragments():
    query = """
    query read0 {
      ... on Query {
        version
      }
    }
    query read1 {
      version
      user {
        ... on Human {
          name
        }
      }
    }
    fragment humanInfo on Human {
      email
    }
    fragment petInfo on Pet {
      name
      owner {
        name
      }
    }
    query read2 {
      matt: user(name: "matt") {
        ...humanInfo
      }
      andy: user(name: "andy") {
        ...humanInfo
        address {
          city
        }
      }
    }
    query read3 {
      matt: user(name: "matt") {
        ...humanInfo
      }
      andy: user(name: "andy") {
        ... on Human {
          email
        }
        address {
          city
        }
        pets {
          ...petInfo
        }
      }
    }
  """

    expected = {"read0": 0, "read1": 1, "read2": 2, "read3": 3}

    errors, result = run_query(query, 10)
    assert not errors
    assert result == expected


def test_should_ignore_the_introspection_query():
    errors, result = run_query(get_introspection_query(), 10)
    assert not errors
    assert result == {"IntrospectionQuery": 0}


def test_should_catch_query_thats_too_deep():
    query = """{
    user {
      pets {
        owner {
          pets {
            owner {
              pets {
                name
              }
            }
          }
        }
      }
    }
    }
    """
    errors, result = run_query(query, 4)

    assert len(errors) == 1
    assert errors[0].message == "'' exceeds maximum operation depth of 4"


def test_should_ignore_field():
    query = """
    query read1 {
      user { address { city } }
    }
    query read2 {
      user1 { address { city } }
      user2 { address { city } }
      user3 { address { city } }
    }
    """

    errors, result = run_query(
        query,
        10,
        {
            "ignore": [
                "user1",
                re.compile("user2"),
                lambda field_name: field_name == "user3",
            ]
        },
    )

    expected = {"read1": 2, "read2": 0}
    assert not errors
    assert result == expected
