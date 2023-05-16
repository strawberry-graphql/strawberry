from typing import Optional

import strawberry
from strawberry.extensions.max_tokens import MaxTokensLimiter


@strawberry.type
class Human:
    name: str
    email: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self, name: Optional[str] = None, email: Optional[str] = None) -> Human:
        return Human(name="Jane Doe", email="jane@example.com")

    version: str
    user1: Human
    user2: Human
    user3: Human


def test_1_more_token_than_allowed():
    query = """
    {
      matt: user(name: "matt") {
        name
        email
      }
    }
    """

    result = _execute_with_max_tokens(query, 13)

    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == "Syntax Error: Document contains more than 13 tokens. Parsing aborted."
    )


def test_no_errors_exactly_max_number_of_tokens():
    query = """
    {
      matt: user(name: "matt") {
        name
      }
    }
    """

    result = _execute_with_max_tokens(query, 13)

    assert not result.errors
    assert result.data


def _execute_with_max_tokens(query: str, max_token_count: int):
    schema = strawberry.Schema(
        Query, extensions=[MaxTokensLimiter(max_token_count=max_token_count)]
    )

    return schema.execute_sync(query)
