from enum import Enum
from pathlib import Path

import strawberry
from strawberry.codegen import QueryCodegen
from strawberry.codegen.plugins.python import PythonPlugin


def test_enum_variable_uses_deterministic_type_order(tmp_path: Path) -> None:
    @strawberry.enum
    class Order(Enum):
        CREATED_AT = "createdAt"

    @strawberry.type
    class Issue:
        id: strawberry.ID

    @strawberry.type
    class Query:
        @strawberry.field
        def issues(self, order_by: Order | None = None) -> list[Issue]:
            return []

    generator = QueryCodegen(
        strawberry.Schema(query=Query),
        plugins=[PythonPlugin(tmp_path / "issues.graphql")],
    )
    code = generator.run(
        "query Issues($orderBy: Order) { issues(orderBy: $orderBy) { id } }"
    ).to_string()

    classes = [
        line.removeprefix("class ").split("(", 1)[0].removesuffix(":")
        for line in code.splitlines()
        if line.startswith("class ")
    ]
    assert classes == ["IssuesResultIssues", "IssuesResult", "Order", "IssuesVariables"]
