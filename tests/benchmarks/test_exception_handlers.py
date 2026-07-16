import pytest
from pytest_codspeed.plugin import BenchmarkFixture

import strawberry


class ValidationError(Exception):
    pass


@strawberry.type
class ErrorResult:
    message: str


@strawberry.type
class Value:
    amount: int


class Handler(strawberry.ExceptionHandler[ValidationError, ErrorResult]):
    def handle(self, exception: ValidationError, *, field, info) -> ErrorResult:
        return ErrorResult(message=str(exception))


@strawberry.type
class Item:
    index: int

    @strawberry.field
    def plain(self, multiplier: int = 1) -> int:
        # No handler applies (the return type is not a union containing
        # ``ErrorResult``), so this exercises the fast path even when the schema
        # has handlers configured.
        return self.index * multiplier

    @strawberry.field
    def checked(self) -> Value | ErrorResult:
        # A handler applies here, so this exercises the exception-handling
        # wrapping. The resolver never raises, so it measures the steady-state
        # overhead of the wrapping, not the conversion itself.
        return Value(amount=self.index)


@strawberry.type
class Query:
    @strawberry.field
    def items(self, count: int) -> list[Item]:
        return [Item(index=i) for i in range(count)]


PLAIN_QUERY = "query ($count: Int!) { items(count: $count) { plain(multiplier: 2) } }"
CHECKED_QUERY = "query ($count: Int!) { items(count: $count) { checked { ... on Value { amount } } } }"


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "handlers",
    [False, True],
    ids=lambda x: "with_handlers" if x else "no_handlers",
)
def test_plain_resolver_field(benchmark: BenchmarkFixture, handlers: bool):
    # Measures whether configuring handlers adds per-field overhead to a field
    # they never apply to (the "existing schemas pay nothing" claim).
    schema = strawberry.Schema(
        query=Query, exception_handlers=[Handler()] if handlers else []
    )

    def run():
        return schema.execute_sync(PLAIN_QUERY, variable_values={"count": 2_000})

    result = benchmark(run)
    assert result.errors is None


@pytest.mark.benchmark
def test_handled_union_field(benchmark: BenchmarkFixture):
    # Measures the steady-state cost of the exception-handling wrapping on a
    # field a handler applies to (no exception is actually raised).
    schema = strawberry.Schema(query=Query, exception_handlers=[Handler()])

    def run():
        return schema.execute_sync(CHECKED_QUERY, variable_values={"count": 2_000})

    result = benchmark(run)
    assert result.errors is None
