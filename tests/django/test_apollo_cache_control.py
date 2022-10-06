import pytest


@pytest.mark.parametrize(
    "query, expected_max_age",
    [
        (
            """# maxAge: 0
# Query.book doesn't set a maxAge and it's a root field (default 0).
query GetBookTitle {
  book {        # 0
    cachedTitle # 30
  }
}
""",
            30,
        ),
        (
            """# maxAge: 60
# Query.cachedBook has a maxAge of 60, and Book.title is a scalar, so it
# inherits maxAge from its parent by default.
query GetCachedBookTitle {
  cachedBook { # 60
    title      # inherits
  }
}
         """,
            60,
        ),
        (
            """# maxAge: 30
# Query.cachedBook has a maxAge of 60, but Book.cachedTitle has
# a maxAge of 30.
query GetCachedBookCachedTitle {
  cachedBook {  # 60
    cachedTitle # 30
  }
}""",
            30,
        ),
        (
            """# maxAge: 40
# Query.reader has a maxAge of 40. Reader.Book is set to
# inheritMaxAge from its parent, and Book.title is a scalar
# that inherits maxAge from its parent by default.
query GetReaderBookTitle {
  reader {  # 40
    book {  # inherits
      title # inherits
    }
  }
}""",
            40,
        ),
    ],
)
def test_apollo_cache_control(graphql_client, query, expected_max_age):
    response = graphql_client.query(query=query)

    assert response.extensions == {"example": "example", "max_age": expected_max_age}
