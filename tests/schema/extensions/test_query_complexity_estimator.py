from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

import strawberry
from strawberry.extensions import (
    ConstantFieldComplexityEstimator,
    FieldComplexityEstimator,
    QueryComplexityEstimator,
)
from strawberry.extensions.query_complexity_estimator import (
    SimpleFieldComplexityEstimator,
)
from strawberry.types import ExecutionContext


@strawberry.type
class Address:
    street: str
    number: int
    city: str
    country: str


@strawberry.type
class Home:
    color: str
    number_of_rooms: int
    address: Address

    @strawberry.field(extensions=[ConstantFieldComplexityEstimator(complexity=42)])
    def address_constant(self) -> Address:
        return self.address


@strawberry.type
class Human:
    name: str
    email: str
    home: Home

    @strawberry.field(extensions=[SimpleFieldComplexityEstimator(scalar_complexity=5)])
    def home_simple(self) -> Home:
        return self.home

    @strawberry.field(extensions=[ConstantFieldComplexityEstimator(complexity=3)])
    def echo(self, say: str) -> str:
        return say


# bad ending: humanity has collapsed, there are only 20 humans alive
ALL_HUMANS = [
    Human(
        name=f"Human {i}",
        email="human{i}@humanity.com",
        home=Home(
            color="red",
            number_of_rooms=i,
            address=Address(
                street="Homo Sapiens st", number=i, city="Humanland", country="Humania"
            ),
        ),
    )
    for i in range(20)
]


@strawberry.type
class Query:
    @strawberry.field
    def humans(self, page_size: int) -> List[Human]:
        return ALL_HUMANS[:page_size]

    @strawberry.field(extensions=[SimpleFieldComplexityEstimator(scalar_complexity=5)])
    def humans_simple(self) -> List[Human]:
        return ALL_HUMANS

    @strawberry.field(extensions=[ConstantFieldComplexityEstimator(complexity=12)])
    def home_constant(self, index: int) -> Home:
        return ALL_HUMANS[index].home


class DefaultFieldComplexityEstimator(FieldComplexityEstimator):
    """Test estimator.

    All scalar fields cost 10, object fields cost the sum of their children. Paginated
    fields, (i.e fields with `page_size` kwarg) multiply their cost by the length of the
    page.
    """

    def estimate_complexity(
        self, child_complexities: Iterator[int], arguments: Dict[str, Any]
    ) -> int:
        children_sum = sum(child_complexities)

        if children_sum == 0:
            return 10

        if "page_size" in arguments:
            page_size = arguments["page_size"]
            assert isinstance(page_size, int)
            return page_size * children_sum

        return children_sum


def get_schema_and_estimator(
    callback: Optional[Callable[[Dict[str, int], ExecutionContext], None]],
    response_key: Optional[str],
) -> Tuple[strawberry.Schema, QueryComplexityEstimator]:
    estimator = QueryComplexityEstimator(
        default_estimator=DefaultFieldComplexityEstimator(),
        response_key=response_key,
        callback=callback,
    )
    schema = strawberry.Schema(
        Query,
        extensions=[estimator],
    )
    return schema, estimator


def test_response_key_is_empty_if_not_provided() -> None:
    """Ensure that QueryComplexityEstimator does not accidentally leak complexities to client if the response_key is not set."""
    query = """
    {
      humans(pageSize: 20) {
        name
      }
    }
    """

    schema, _ = get_schema_and_estimator(None, None)

    result = schema.execute_sync(query)
    assert result.extensions == {}


def test_response_key_is_populated_if_provided() -> None:
    """Ensure that QueryComplexityEstimator returns expected values to the client if response_key is set."""
    query = """
    {
      humans(pageSize: 20) {
        name
      }
    }
    """

    schema, _ = get_schema_and_estimator(None, "my_key")

    result = schema.execute_sync(query)
    assert result.extensions is not None
    assert result.extensions["myKey"] == {"anonymous": 10 * 20}


def test_callback_gets_called_with_data() -> None:
    """Ensure that the callback arg for QueryComplexityEstimator gets called with proper values."""
    query = """
    {
      humans(pageSize: 20) {
        name
      }
    }
    """

    called_with: Optional[Dict[str, int]] = None

    def callback(complexities: Dict[str, int], _: ExecutionContext) -> None:
        nonlocal called_with
        called_with = complexities

    schema, _ = get_schema_and_estimator(callback, None)

    _ = schema.execute_sync(query)
    assert called_with == {"anonymous": 10 * 20}


def test_nested_object_with_page_size() -> None:
    """Ensure that a custom FieldComplexityEstimator works with deep queries."""
    query = """
    {
      humans(pageSize: 10) {
        name
        home {
          color
          numberOfRooms
          address {
            street
            number
          }
        }
      }
    }
    """

    schema, estimator = get_schema_and_estimator(None, None)

    _ = schema.execute_sync(query)
    assert estimator.results == {
        "anonymous": (
            10
            * (  # pageSize
                10  # name
                + 10
                + 10  # color + numberOfRooms
                + 10
                + 10  # street + number
            )
        )
    }


def test_constant_field_complexity_estimator() -> None:
    """Ensure that the ConstantFieldComplexityEstimator works as expected."""
    query = """
    {
      homeConstant {
        color
        numberOfRooms
        address {
          country
          city
          street
          number
        }
      }
    }
    """

    schema, estimator = get_schema_and_estimator(None, None)

    _ = schema.execute_sync(query)
    assert estimator.results == {
        "anonymous": 12  # homeConstant, ConstantFieldComplexityEstimator
    }


def test_simple_field_complexity_estimator() -> None:
    """Ensure that the SimpleFieldComplexityEstimator works as expected."""
    query = """
    {
      humansSimple {
        name
        home {
          color
          numberOfRooms
        }
      }
    }
    """

    schema, estimator = get_schema_and_estimator(None, None)

    _ = schema.execute_sync(query)
    assert estimator.results == {
        "anonymous": (
            5  # name, SimpleFieldComplexityEstimator
            + 10
            + 10  # color + numberOfRooms, DefaultFieldComplexityEstimator
        )
    }


def test_field_estimator_complexity_selection_deep() -> None:
    """Ensure that the correct estimator gets picked for each field in a deep query."""
    query = """
    {
      humans(pageSize: 2) {
        name
        homeSimple {
          color
          numberOfRooms
          addressConstant {
            country
            city
            street
            number
          }
          address {
            country
            city
          }
        }
      }
    }
    """

    schema, estimator = get_schema_and_estimator(None, None)

    _ = schema.execute_sync(query)
    assert estimator.results == {
        "anonymous": (
            2
            * (  # humans(pageSize), DefaultFieldComplexityEstimator
                10  # name, DefaultFieldComplexityEstimator
                + (  # homeSimple, SimpleFieldComplexityEstimator
                    5
                    + 5  # color + numberOfRooms, SimpleFieldComplexityEstimator
                    + 42  # addressConstant, ConstantFieldComplexityEstimator
                    + 10
                    + 10  # address, DefaultFieldComplexityEstimator
                )
            )
        )
    }


def test_query_variables() -> None:
    """Ensure that QueryComplexityEstimator calls estimators with input variable values."""
    query = """
    query myQuery($pageSize: Int!) {
      humans(pageSize: $pageSize) {
        name
      }
    }
    """

    schema, estimator = get_schema_and_estimator(None, None)

    page_size = 7
    _ = schema.execute_sync(query, {"pageSize": page_size})
    assert estimator.results == {"myQuery": 10 * page_size}


def test_query_fragment_simple() -> None:
    """Ensure that QueryComplexityEstimator handles fragments."""
    query = """
    fragment hooman on Human {
      name
      home {
        color
        numberOfRooms
      }
    }
    query myQuery {
      humans(pageSize: 10) {
        ...hooman
      }
    }
    """

    schema, estimator = get_schema_and_estimator(None, None)

    _ = schema.execute_sync(query)
    assert estimator.results == {"myQuery": 10 * (10 + 10 + 10)}


def test_query_fragment_root() -> None:
    """Ensure that QueryComplexityEstimator handles fragments on the root Query type."""
    query = """
    fragment frag on Query {
      homeConstant {
        color
      }
    }
    query myQuery {
      ...frag
    }
    """

    schema, estimator = get_schema_and_estimator(None, None)

    _ = schema.execute_sync(query)
    assert estimator.results == {"myQuery": 12}


def test_query_fragment_with_variables() -> None:
    """Ensure that QueryComplexityEstimator handles fragments which use variables."""
    query = """
    fragment hooman on Human{
      echo(say: $say)
    }
    query myQuery($say: String!, $pageSize: Int!) {
      humans(pageSize: $pageSize) {
        ...hooman
      }
    }
    """

    schema, estimator = get_schema_and_estimator(None, None)

    page_size = 7
    _ = schema.execute_sync(query, {"say": "hello", "pageSize": page_size})
    assert estimator.results == {"myQuery": page_size * 3}


def test_query_fragment_nested_dependency() -> None:
    """Ensure that QueryComplexityEstimator handles fragments that depend on other fragments."""
    query = """
    fragment hooman on Human {
      name
      home {
        ...home
      }
    }
    fragment addr on Address {
      country
    }
    fragment home on Home {
      color
      numberOfRooms
      address {
        ...addr
      }
    }
    query myQuery {
      humans(pageSize: 10) {
        ...hooman
      }
    }
    """
    # NOTE: fragments are defined out of order on purpose to test whether the parser
    # order affects results

    schema, estimator = get_schema_and_estimator(None, None)

    _ = schema.execute_sync(query)
    assert estimator.results == {"myQuery": 10 * (10 + 10 + 10 + 10)}
