from strawberry.types.graphql import OperationType
from strawberry.utils.operation import get_operation_type
from graphql import parse

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



def test_get_operation_type_with_fragment_name_collision():
    assert get_operation_type(
        query_collision,
        'UserAgent'
    ) == OperationType.QUERY
    assert get_operation_type(
        query_no_collision,
        'UserAgent'
    ) == OperationType.QUERY
    assert get_operation_type(
        mutation_collision,
        'UserAgent'
    ) == OperationType.MUTATION
    assert get_operation_type(
        mutation_no_collision,
        'UserAgent'
    ) ==  OperationType.MUTATION
    assert get_operation_type(
        subscription_collision,
        'UserAgent'
    ) == OperationType.SUBSCRIPTION
    assert get_operation_type(
        subscription_no_collision,
        'UserAgent'
    ) == OperationType.SUBSCRIPTION

    assert get_operation_type(query_collision) == OperationType.QUERY
    assert get_operation_type(mutation_collision) == OperationType.MUTATION
    assert get_operation_type(subscription_collision) == OperationType.SUBSCRIPTION
