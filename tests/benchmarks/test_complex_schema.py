import pytest
from asgiref.sync import async_to_sync
from pytest_codspeed.plugin import BenchmarkFixture

from .schema import schema

query = """
fragment AuthorFragment on User {
  id
  username
  email
  role
}

fragment PostFragment on Post {
  id
  content
  title

  author {
    ...AuthorFragment
  }

  comments {
    edges {
      node {
        author {
          id
          username
          email
          role
        }
      }
    }
  }
}

query Query($query: String!, $first: Int!) {
  search(query: $query, first: $first) {
    ... on User {
      id
      username
      email
      role
      posts {
        pageInfo {
          hasNextPage
          hasPreviousPage
          startCursor
          endCursor
        }
        edges {
          cursor
          node {
            author {
              email
              id
              posts {
                edges {
                  node {
                    ...PostFragment
                  }
                }
              }
            }
          }
        }
      }
    }
    ... on Post {
      ...PostFragment
    }
    ... on Comment {
      id
      text
      author {
        ...AuthorFragment
      }
      post {
        ...PostFragment
      }
    }
  }
}
"""


@pytest.mark.parametrize("number", [50])
def test_interface_performance(benchmark: BenchmarkFixture, number: int):
    result = benchmark(
        async_to_sync(schema.execute),
        query,
        variable_values={"query": "test", "first": number},
    )

    assert not result.errors
