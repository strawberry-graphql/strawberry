#!/usr/bin/env python3
#
from strawberry import strawberry
from strawberry.extensions import PyInstrument


def test_basic_pyinstrument():
    @strawberry.type
    class Query:
        @strawberry.field
        def the_field(self) -> int:
            return 3

    schema = strawberry.Schema(
        query=Query, extensions=[PyInstrument(report_path="/tmp/pyinstrument.html")]
    )

    result = schema.execute_sync("{ theField }")

    assert not result.errors
