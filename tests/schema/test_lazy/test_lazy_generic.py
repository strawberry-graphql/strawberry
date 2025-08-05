import os
import subprocess
import sys
import sysconfig
import textwrap
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Generic, Optional, TypeVar

import pytest

import strawberry

if TYPE_CHECKING:
    from tests.schema.test_lazy.type_a import TypeA
    from tests.schema.test_lazy.type_c import TypeC

STRAWBERRY_EXECUTABLE = next(
    Path(sysconfig.get_path("scripts")).glob("strawberry*"), None
)

T = TypeVar("T")

TypeAType = Annotated["TypeA", strawberry.lazy("tests.schema.test_lazy.type_a")]


def test_lazy_types_with_generic():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        users: Edge[TypeAType]

    strawberry.Schema(query=Query)


def test_no_generic_type_duplication_with_lazy():
    from tests.schema.test_lazy.type_b import TypeB

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        users: Edge[TypeB]
        relatively_lazy_users: Edge[Annotated["TypeB", strawberry.lazy(".type_b")]]
        absolutely_lazy_users: Edge[
            Annotated["TypeB", strawberry.lazy("tests.schema.test_lazy.type_b")]
        ]

    schema = strawberry.Schema(query=Query)

    expected_schema = textwrap.dedent(
        """
        type Query {
          users: TypeBEdge!
          relativelyLazyUsers: TypeBEdge!
          absolutelyLazyUsers: TypeBEdge!
        }

        type TypeA {
          listOfB: [TypeB!]
          typeB: TypeB!
        }

        type TypeB {
          typeA: TypeA!
          typeAList: [TypeA!]!
          typeCList: [TypeC!]!
        }

        type TypeBEdge {
          node: TypeB!
        }

        type TypeC {
          name: String!
        }
        """
    ).strip()

    assert str(schema) == expected_schema


@pytest.mark.parametrize(
    "commands",
    [
        pytest.param(
            [sys.executable, "tests/schema/test_lazy/type_c.py"],
            id="script",
        ),
        pytest.param(
            [sys.executable, "-m", "tests.schema.test_lazy.type_c"],
            id="module",
        ),
        pytest.param(
            [STRAWBERRY_EXECUTABLE, "export-schema", "tests.schema.test_lazy.schema"],
            id="cli",
            marks=pytest.mark.skipif(
                sys.platform == "win32", reason="Test is broken on windows"
            ),
        ),
    ],
)
def test_lazy_types_loaded_from_same_module(commands: Sequence[str]):
    """Test if lazy types resolved from the same module produce duplication error.

    Note:
      `subprocess` is used since the test must be run as the main module / script.
    """
    result = subprocess.run(
        args=[*commands],
        env=os.environ,
        capture_output=True,
        check=True,
    )

    expected = """\
    type Query {
      typeA: TypeCEdge!
      typeB: TypeCEdge!
    }

    type TypeC {
      name: String!
    }

    type TypeCEdge {
      node: TypeC!
    }
    """

    schema_sdl = result.stdout.decode().replace(os.linesep, "\n")
    assert textwrap.dedent(schema_sdl) == textwrap.dedent(expected)


def test_lazy_types_declared_within_optional():
    from tests.schema.test_lazy.type_c import Edge, TypeC

    @strawberry.type
    class Query:
        normal_edges: list[Edge[Optional[TypeC]]]
        lazy_edges: list[
            Edge[
                Optional[
                    Annotated["TypeC", strawberry.lazy("tests.schema.test_lazy.type_c")]
                ]
            ]
        ]

    schema = strawberry.Schema(query=Query)
    expected_schema = textwrap.dedent(
        """
        type Query {
          normalEdges: [TypeCOptionalEdge!]!
          lazyEdges: [TypeCOptionalEdge!]!
        }

        type TypeC {
          name: String!
        }

        type TypeCOptionalEdge {
          node: TypeC
        }
        """
    ).strip()

    assert str(schema) == expected_schema


def test_lazy_with_already_specialized_generic():
    from tests.schema.test_lazy.type_d import Query

    schema = strawberry.Schema(query=Query)
    expected_schema = textwrap.dedent(
        """
        type Query {
          typeD1: TypeD!
          typeD: TypeD!
        }

        type TypeD {
          name: String!
        }
        """
    ).strip()

    assert str(schema) == expected_schema
