from graphql import OperationType, parse

from strawberry.utils.operation import get_first_operation, get_operation_type
import pytest
from strawberry.types.graphql import OperationType


def test_document_without_operation_definition_notes():
    document = parse(
        """
        fragment Test on Query {
            hello
        }
    """
    )
    assert get_first_operation(document) is None


def test_single_operation_definition_note():
    document = parse(
        """
        query Operation1 {
            hello
        }
    """
    )
    assert get_first_operation(document) is not None
    assert get_first_operation(document).operation == OperationType.QUERY


def test_multiple_operation_definition_notes():
    document = parse(
        """
        mutation Operation1 {
            hello
        }
        query Operation2 {
            hello
        }
    """
    )
    assert get_first_operation(document) is not None
    assert get_first_operation(document).operation == OperationType.MUTATION


mutation_collision = parse("""
fragment UserAgent on UserAgentType {
  id
}

mutation UserAgent {
  setUserAgent {
    ...UserAgent
  }
}
""")

query_collision = parse("""
fragment UserAgent on UserAgentType {
  id
}

query UserAgent {
  userAgent {
    ...UserAgent
  }
}
""")

subscription_collision = parse("""
fragment UserAgent on UserAgentType {
  id
}

subscription UserAgent {
  userAgent {
    ...UserAgent
  }
}
""")

mutation_no_collision = parse("""
fragment UserAgentFragment on UserAgentType {
  id
}

mutation UserAgent {
  setUserAgent {
    ...UserAgentFragment
  }
}
""")

query_no_collision = parse("""
fragment UserAgentFragment on UserAgentType {
  id
}

query UserAgent {
  userAgent {
    ...UserAgentFragment
  }
}
""")

subscription_no_collision = parse("""
fragment UserAgentFragment on UserAgentType {
  id
}

subscription UserAgent {
  userAgent {
    ...UserAgentFragment
  }
}
""")


@pytest.mark.parametrize(
    ("document", "operation", "expectation"),
    [
        (query_collision, "UserAgent", OperationType.QUERY),
        (query_no_collision, "UserAgent", OperationType.QUERY),
        (mutation_collision, "UserAgent", OperationType.MUTATION),
        (mutation_no_collision, "UserAgent", OperationType.MUTATION),
        (subscription_collision, "UserAgent", OperationType.SUBSCRIPTION),
        (subscription_no_collision, "UserAgent", OperationType.SUBSCRIPTION),
        (query_collision, None, OperationType.QUERY),
        (mutation_collision, None, OperationType.MUTATION),
        (subscription_collision, None, OperationType.SUBSCRIPTION),
    ],
)
def test_get_operation_type_with_fragment_name_collision(
    document, operation, expectation
):
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
