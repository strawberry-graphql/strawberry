import asyncio

import pytest
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
def test_execute_complex_schema_v2(
    benchmark: BenchmarkFixture, number: int, benchmark_loop: asyncio.AbstractEventLoop
):
    def run():
        coroutine = schema.execute(
            query,
            variable_values={"query": "test", "first": number},
        )

        return benchmark_loop.run_until_complete(coroutine)

    result = benchmark(run)

    assert not result.errors

    assert result.data is not None
    assert len(result.data["search"]) == number
