import tempfile
import time
from pathlib import Path

import strawberry
from strawberry.extensions import pyinstrument


def function_called_by_us_a():
    time.sleep(0.1)
    return function_called_by_us_b()


def function_called_by_us_b():
    time.sleep(0.1)
    return function_called_by_us_c()


def function_called_by_us_c():
    time.sleep(0.1)
    return 4


def test_basic_pyinstrument():
    with tempfile.NamedTemporaryFile(delete=False) as report_file:
        report_file_path = Path(report_file.name)

        @strawberry.type
        class Query:
            @strawberry.field
            def the_field(self) -> int:
                return function_called_by_us_a()

        schema = strawberry.Schema(
            query=Query,
            extensions=[pyinstrument.PyInstrument(report_path=report_file_path)],
        )

        # Query the schema
        result = schema.execute_sync("{ theField }")
        content = report_file_path.read_text("utf-8")

    assert not result.errors
    assert result.data
    assert result.data["theField"] == 4

    assert "function_called_by_us_a" in content
    assert "function_called_by_us_b" in content
    assert "function_called_by_us_c" in content

    assert content.count('"sleep') == 3
