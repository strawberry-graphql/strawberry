from pathlib import Path

import pytest

from strawberry.codegen import QueryCodegen
from strawberry.codegen.plugins.print_operation import PrintOperationPlugin

HERE = Path(__file__).parent
QUERIES = list(HERE.glob("queries/*.graphql"))


@pytest.mark.parametrize("query", QUERIES, ids=[x.name for x in QUERIES])
def test_codegen(
    query: Path,
    schema,
):
    generator = QueryCodegen(schema, plugins=[PrintOperationPlugin(query)])
    query_content = query.read_text()

    result = generator.run(query_content)

    assert result.to_string() == query_content
