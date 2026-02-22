import itertools
from collections.abc import Callable
from typing import Any

import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True
nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.14", "3.13", "3.12", "3.11", "3.10"]

GQL_CORE_VERSIONS = [
    "3.2.6",
    "3.3.0a9",
]

COMMON_PYTEST_OPTIONS = [
    "--cov=.",
    "--cov-append",
    "-n",
    "auto",
    "--showlocals",
    "-vv",
    "--ignore=tests/typecheckers",
    "--ignore=tests/cli",
    "--ignore=tests/benchmarks",
    "--ignore=tests/experimental/pydantic",
]

INTEGRATIONS = [
    "asgi",
    "aiohttp",
    "chalice",
    "channels",
    "django",
    "fastapi",
    "flask",
    "quart",
    "sanic",
    "litestar",
    "pydantic",
]


def _install_gql_core(session: nox.Session, version: str) -> None:
    session.install(f"graphql-core=={version}")


gql_core_parametrize = nox.parametrize(
    "gql_core",
    GQL_CORE_VERSIONS,
)


def with_gql_core_parametrize(name: str, params: list[str]) -> Callable[[Any], Any]:
    # github cache doesn't support comma in the name, this is a workaround.
    arg_names = f"{name}, gql_core"
    combinations = list(itertools.product(params, GQL_CORE_VERSIONS))
    ids = [f"{name}-{comb[0]}__graphql-core-{comb[1]}" for comb in combinations]
    return nox.parametrize(arg_names, combinations, ids=ids)


@nox.session(python=PYTHON_VERSIONS, name="Tests", tags=["tests"])
@gql_core_parametrize
def tests(session: nox.Session, gql_core: str) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    _install_gql_core(session, gql_core)
    markers = (
        ["-m", f"not {integration}", f"--ignore=tests/{integration}"]
        for integration in INTEGRATIONS
    )
    markers = [item for sublist in markers for item in sublist]

    session.run(
        "pytest",
        *COMMON_PYTEST_OPTIONS,
        *markers,
    )


@nox.session(python=["3.12"], name="Django tests", tags=["tests"])
@with_gql_core_parametrize("django", ["5.1.3", "5.0.9", "4.2.0"])
def tests_django(session: nox.Session, django: str, gql_core: str) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    _install_gql_core(session, gql_core)
    session.install(f"django~={django}")
    session.install("pytest-django")

    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", "django")


@nox.session(python=["3.11"], name="Starlette tests", tags=["tests"])
@gql_core_parametrize
def tests_starlette(session: nox.Session, gql_core: str) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install("starlette")
    _install_gql_core(session, gql_core)
    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", "asgi")


@nox.session(python=["3.11"], name="Test integrations", tags=["tests"])
@with_gql_core_parametrize(
    "integration",
    [
        "aiohttp",
        "chalice",
        "channels",
        "fastapi",
        "flask",
        "quart",
        "sanic",
        "litestar",
    ],
)
def tests_integrations(session: nox.Session, integration: str, gql_core: str) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install(integration)
    _install_gql_core(session, gql_core)
    if integration == "aiohttp":
        session.install("pytest-aiohttp")
    elif integration == "channels":
        session.install("pytest-django")
        session.install("daphne")

    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", integration)


@nox.session(
    python=["3.10", "3.11", "3.12", "3.13"],
    name="Pydantic V1 tests",
    tags=["tests", "pydantic"],
)
@gql_core_parametrize
def test_pydantic(session: nox.Session, gql_core: str) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install("pydantic~=1.10")
    _install_gql_core(session, gql_core)
    session.run(
        "pytest",
        "--cov=.",
        "--cov-append",
        "-m",
        "pydantic",
        "--ignore=tests/cli",
        "--ignore=tests/benchmarks",
    )


@nox.session(python=PYTHON_VERSIONS, name="Pydantic tests", tags=["tests", "pydantic"])
@gql_core_parametrize
def test_pydantic_v2(session: nox.Session, gql_core: str) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install("pydantic>=2.2")
    _install_gql_core(session, gql_core)
    session.run(
        "pytest",
        "--cov=.",
        "--cov-append",
        "-m",
        "pydantic",
        "--ignore=tests/cli",
        "--ignore=tests/benchmarks",
    )


@nox.session(python=PYTHON_VERSIONS, name="Type checkers tests", tags=["tests"])
def tests_typecheckers(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install("pyright")
    session.install("pydantic")
    session.install("mypy")
    session.install("ty")

    session.run(
        "pytest",
        "--cov=.",
        "--cov-append",
        "tests/typecheckers",
        "-vv",
    )


@nox.session(python=PYTHON_VERSIONS, name="CLI tests", tags=["tests"])
def tests_cli(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install("uvicorn")
    session.install("starlette")

    session.run(
        "pytest",
        "--cov=.",
        "--cov-append",
        "tests/cli",
        "-vv",
    )
