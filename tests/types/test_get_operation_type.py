import pytest
from graphql import parse

from strawberry.types.graphql import OperationType
from strawberry.utils.operation import get_operation_type

mutation_collision = parse("""
fragment UserAgent on UserAgentType {
  id
}

mutation UserAgent {
  getUserAgent {
    ...UserAgent
  }
}
""")

query_collision = parse("""
fragment UserAgent on UserAgentType {
  id
}

query UserAgent {
  getUserAgent {
    ...UserAgent
  }
}
""")

subscription_collision = parse("""
fragment UserAgent on UserAgentType {
  id
}

subscription UserAgent {
  getUserAgent {
    ...UserAgent
  }
}
""")

mutation_no_collision = parse("""
fragment UserAgentFragment on UserAgentType {
  id
}

mutation UserAgent {
  getUserAgent {
    ...UserAgentFragment
  }
}
""")

query_no_collision = parse("""
fragment UserAgentFragment on UserAgentType {
  id
}

query UserAgent {
  getUserAgent {
    ...UserAgentFragment
  }
}
""")

subscription_no_collision = parse("""
fragment UserAgentFragment on UserAgentType {
  id
}

subscription UserAgent {
  getUserAgent {
    ...UserAgentFragment
  }
}
""")


@pytest.mark.parametrize(("document", "operation", "expectation"), [
    (query_collision, "UserAgent", OperationType.QUERY),
    (query_no_collision, "UserAgent", OperationType.QUERY),
    (mutation_collision, "UserAgent", OperationType.MUTATION),
    (mutation_no_collision, "UserAgent", OperationType.MUTATION),
    (subscription_collision, "UserAgent", OperationType.SUBSCRIPTION),
    (subscription_no_collison, "UserAgent", OperationType.SUBSCRIPTION),
    (query_collision, None, OperationType.QUERY),
    (mutation_collision, None, OperationType.MUTATION)
    (subscription_collision, None, OperationType.SUBSCRIPTION),
])    
def test_get_operation_type_with_fragment_name_collision(document, operation, expectation):
    assert get_operation_type(document, operation) == expectation


def test_get_operation_type_only_fragments():
    only_fragments = parse("""
      fragment Foo on Bar {
        id
      }
    """)

    with pytest.raises(RuntimeError) as excinfo:
        get_operation_type(only_fragments)

    assert "Can't get GraphQL operation type" in str(excinfo.value)
