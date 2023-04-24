#!/usr/bin/env python3
#
from strawberry.extensions import pyinstrument
import strawberry
import time


def a():
    time.sleep(0.1)
    return b()


def b():
    time.sleep(0.1)
    return c()


def c():
    time.sleep(0.1)
    return 4


def test_basic_pyinstrument():
    REPORT_PATH = "/tmp/pyinstrument.html"

    @strawberry.type
    class Query:
        @strawberry.field
        def the_field(self) -> int:
            return a()

    schema = strawberry.Schema(
        query=Query,
        extensions=[pyinstrument.PyInstrument(report_path=REPORT_PATH)],
    )

    # Query the schema
    result = schema.execute_sync("{ theField }")

    assert not result.errors
    assert result.data["theField"] == 4

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        assert "a()" in content
        assert "b()" in content
        assert "c()" in content
        assert content.count('"function": "sleep"') == 3
