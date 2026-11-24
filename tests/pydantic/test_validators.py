from datetime import date
from typing import Annotated, Any

import pydantic
from pydantic import AfterValidator, BeforeValidator

import strawberry
from strawberry.scalars import JSON


def test_validators_change_the_values_resolvers_get():
    @strawberry.pydantic.input
    class PostInput(pydantic.BaseModel):
        title: str
        author: Annotated[str, AfterValidator(str.lower)]
        tags: Annotated[list[str], BeforeValidator(lambda tags: sorted(set(tags)))]

        @pydantic.field_validator("title")
        @classmethod
        def capitalize(cls, title: str) -> str:
            return title.capitalize()

    @strawberry.type
    class Query:
        @strawberry.field
        def post(self, input: PostInput) -> str:
            return repr(input)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        '{ post(input: {title: "hello", author: "ADA", tags: ["b", "a", "b"]}) }'
    )

    assert not result.errors
    assert result.data == {
        "post": "PostInput(title='Hello', author='ada', tags=['a', 'b'])"
    }


def test_errors_of_validators_are_located_at_what_they_validate():
    @strawberry.pydantic.input
    class DateRangeInput(pydantic.BaseModel):
        start_date: date
        end_date: date

        @pydantic.model_validator(mode="after")
        def check_dates(self) -> "DateRangeInput":
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before end_date")

            return self

    @strawberry.pydantic.input
    class SearchInput(pydantic.BaseModel):
        query: str
        dates: DateRangeInput

        @pydantic.field_validator("query")
        @classmethod
        def check_query(cls, query: str) -> str:
            if not query.strip():
                raise ValueError("query can't be blank")

            return query

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, input: SearchInput) -> bool:
            return True

        @strawberry.field
        def count(self, range: DateRangeInput) -> int:
            return 0

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        {
            search(input: {
                query: " "
                dates: {startDate: "2024-12-31", endDate: "2024-01-01"}
            })
        }
        """
    )

    assert result.errors
    assert result.errors[0].extensions["validationErrors"] == [
        {
            "location": ["input", "query"],
            "message": "query can't be blank",
            "type": "value_error",
        },
        {
            "location": ["input", "dates"],
            "message": "start_date must be before end_date",
            "type": "value_error",
        },
    ]

    result = schema.execute_sync(
        '{ count(range: {startDate: "2024-12-31", endDate: "2024-01-01"}) }'
    )

    assert result.errors
    assert result.errors[0].extensions["validationErrors"] == [
        {
            "location": ["range"],
            "message": "start_date must be before end_date",
            "type": "value_error",
        }
    ]


def test_before_validators_receive_python_names():
    received: list[Any] = []

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        user_name: str = pydantic.Field(alias="login")
        display_name: str | None = None

        @pydantic.model_validator(mode="before")
        @classmethod
        def default_display_name(cls, data: Any) -> Any:
            received.append(data)

            return {**data, "display_name": data["user_name"]}

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, input: UserInput) -> str:
            return repr(input)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ user(input: {userName: "ada"}) }')

    assert not result.errors
    assert result.data == {"user": "UserInput(user_name='ada', display_name='ada')"}
    assert received == [{"user_name": "ada", "display_name": None}]


def test_model_config_applies_to_graphql_inputs():
    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        # GraphQL rejects unknown fields and supplies published defaults for
        # fields the client didn't send.
        model_config = pydantic.ConfigDict(extra="forbid", str_strip_whitespace=True)

        name: str
        bio: str | None = None

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, input: UserInput) -> str:
            return repr(input)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ user(input: {name: "  Ada "}) }')

    assert not result.errors
    assert result.data == {"user": "UserInput(name='Ada', bio=None)"}


def test_strict_mode_applies_to_values_graphql_does_not_check():
    @strawberry.pydantic.input
    class ScoreInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)

        name: str
        # GraphQL doesn't validate the values of JSON scalars
        score: Annotated[int, strawberry.field(graphql_type=JSON)]

    @strawberry.type
    class Query:
        @strawberry.field
        def score(self, input: ScoreInput) -> int:
            return input.score

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ score(input: {name: "Ada", score: 1}) }')

    assert not result.errors
    assert result.data == {"score": 1}

    result = schema.execute_sync('{ score(input: {name: "Ada", score: "1"}) }')

    assert result.errors
    assert result.errors[0].extensions["validationErrors"] == [
        {
            "location": ["input", "score"],
            "message": "Input should be a valid integer",
            "type": "int_type",
        }
    ]
