from typing import Optional, Union

import pytest
from graphql import (
    GraphQLError,
    get_introspection_query,
    parse,
    specified_rules,
    validate,
)

import strawberry
from strawberry.extensions import QueryDepthLimiter
from strawberry.extensions.query_depth_limiter import (
    IgnoreContext,
    ShouldIgnoreType,
    create_validator,
)


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
    pets: list[Pet]


@strawberry.input
class Biography:
    name: str
    owner_name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(
        self,
        name: Optional[str],
        id: Optional[int],
        age: Optional[float],
        is_cool: Optional[bool],
    ) -> Human:
        pass

    @strawberry.field
    def users(self, names: Optional[list[str]]) -> list[Human]:
        pass

    @strawberry.field
    def cat(bio: Biography) -> Cat:
        pass

    version: str
    user1: Human
    user2: Human
    user3: Human


schema = strawberry.Schema(Query)


def run_query(
    query: str, max_depth: int, should_ignore: ShouldIgnoreType = None
) -> tuple[list[GraphQLError], Union[dict[str, int], None]]:
    document = parse(query)

    result = None

    def callback(query_depths):
        nonlocal result
        result = query_depths

    validation_rule = create_validator(max_depth, should_ignore, callback)

    errors = validate(
        schema._schema,
        document,
        rules=(*specified_rules, validation_rule),
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
    assert errors[0].message == "'anonymous' exceeds maximum operation depth of 4"


def test_should_raise_invalid_ignore():
    with pytest.raises(
        TypeError,
        match="The `should_ignore` argument to `QueryDepthLimiter` must be a callable.",
    ):
        strawberry.Schema(
            Query, extensions=[QueryDepthLimiter(max_depth=10, should_ignore=True)]
        )


def test_should_ignore_field_by_name():
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

    def should_ignore(ignore: IgnoreContext) -> bool:
        return ignore.field_name in ("user1", "user2", "user3")

    errors, result = run_query(query, 10, should_ignore=should_ignore)

    expected = {"read1": 2, "read2": 0}
    assert not errors
    assert result == expected


def test_should_ignore_field_by_str_argument():
    query = """
    query read1 {
      user(name:"matt") { address { city } }
    }
    query read2 {
      user1 { address { city } }
      user2 { address { city } }
      user3 { address { city } }
    }
    """

    def should_ignore(ignore: IgnoreContext) -> bool:
        return ignore.field_args.get("name") == "matt"

    errors, result = run_query(query, 10, should_ignore=should_ignore)

    expected = {"read1": 0, "read2": 2}
    assert not errors
    assert result == expected


def test_should_ignore_field_by_int_argument():
    query = """
    query read1 {
      user(id:1) { address { city } }
    }
    query read2 {
      user1 { address { city } }
      user2 { address { city } }
      user3 { address { city } }
    }
    """

    def should_ignore(ignore: IgnoreContext) -> bool:
        return ignore.field_args.get("id") == 1

    errors, result = run_query(query, 10, should_ignore=should_ignore)

    expected = {"read1": 0, "read2": 2}
    assert not errors
    assert result == expected


def test_should_ignore_field_by_float_argument():
    query = """
    query read1 {
      user(age:10.5) { address { city } }
    }
    query read2 {
      user1 { address { city } }
      user2 { address { city } }
      user3 { address { city } }
    }
    """

    def should_ignore(ignore: IgnoreContext) -> bool:
        return ignore.field_args.get("age") == 10.5

    errors, result = run_query(query, 10, should_ignore=should_ignore)

    expected = {"read1": 0, "read2": 2}
    assert not errors
    assert result == expected


def test_should_ignore_field_by_bool_argument():
    query = """
    query read1 {
      user(isCool:false) { address { city } }
    }
    query read2 {
      user1 { address { city } }
      user2 { address { city } }
      user3 { address { city } }
    }
    """

    def should_ignore(ignore: IgnoreContext) -> bool:
        return ignore.field_args.get("isCool") is False

    errors, result = run_query(query, 10, should_ignore=should_ignore)

    expected = {"read1": 0, "read2": 2}
    assert not errors
    assert result == expected


def test_should_ignore_field_by_name_and_str_argument():
    query = """
    query read1 {
      user(name:"matt") { address { city } }
    }
    query read2 {
      user1 { address { city } }
      user2 { address { city } }
      user3 { address { city } }
    }
    """

    def should_ignore(ignore: IgnoreContext) -> bool:
        return ignore.field_args.get("name") == "matt"

    errors, result = run_query(query, 10, should_ignore=should_ignore)

    expected = {"read1": 0, "read2": 2}
    assert not errors
    assert result == expected


def test_should_ignore_field_by_list_argument():
    query = """
    query read1 {
      users(names:["matt","andy"]) { address { city } }
    }
    query read2 {
      user1 { address { city } }
      user2 { address { city } }
      user3 { address { city } }
    }
    """

    def should_ignore(ignore: IgnoreContext) -> bool:
        return "matt" in ignore.field_args.get("names", [])

    errors, result = run_query(query, 10, should_ignore=should_ignore)

    expected = {"read1": 0, "read2": 2}
    assert not errors
    assert result == expected


def test_should_ignore_field_by_object_argument():
    query = """
    query read1 {
      cat(bio:{
        name:"Momo",
        ownerName:"Tommy"
      }) { name }
    }
    query read2 {
      user1 { address { city } }
      user2 { address { city } }
      user3 { address { city } }
    }
    """

    def should_ignore(ignore: IgnoreContext) -> bool:
        return ignore.field_args.get("bio", {}).get("name") == "Momo"

    errors, result = run_query(query, 10, should_ignore=should_ignore)

    expected = {"read1": 0, "read2": 2}
    assert not errors
    assert result == expected


def test_should_work_as_extension():
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

    def should_ignore(ignore: IgnoreContext) -> bool:
        return False

    schema = strawberry.Schema(
        Query, extensions=[QueryDepthLimiter(max_depth=4, should_ignore=should_ignore)]
    )

    result = schema.execute_sync(query)

    assert len(result.errors) == 1
    assert (
        result.errors[0].message == "'anonymous' exceeds maximum operation depth of 4"
    )
