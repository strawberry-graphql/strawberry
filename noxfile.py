import itertools
from typing import Any, Callable

import nox
from nox_poetry import Session, session

nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True
nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.13", "3.12", "3.11", "3.10", "3.9"]

GQL_CORE_VERSIONS = [
    "3.2.3",
    "3.3.0a6",
]

COMMON_PYTEST_OPTIONS = [
    "--cov=.",
    "--cov-append",
    "--cov-report=xml",
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


def _install_gql_core(session: Session, version: str) -> None:
    session._session.install(f"graphql-core=={version}")


gql_core_parametrize = nox.parametrize(
    "gql_core",
    GQL_CORE_VERSIONS,
)


def with_gql_core_parametrize(name: str, params: list[str]) -> Callable[[Any], Any]:
    # github cache doesn't support comma in the name, this is a workaround.
    arg_names = f"{name}, gql_core"
    combinations = list(itertools.product(params, GQL_CORE_VERSIONS))
    ids = [f"{name}-{comb[0]}__graphql-core-{comb[1]}" for comb in combinations]
    return lambda fn: nox.parametrize(arg_names, combinations, ids=ids)(fn)


@session(python=PYTHON_VERSIONS, name="Tests", tags=["tests"])
@gql_core_parametrize
def tests(session: Session, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)
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


@session(python=["3.12"], name="Django tests", tags=["tests"])
@with_gql_core_parametrize("django", ["5.1.3", "5.0.9", "4.2.0"])
def tests_django(session: Session, django: str, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)
    _install_gql_core(session, gql_core)
    session._session.install(f"django~={django}")  # type: ignore
    session._session.install("pytest-django")  # type: ignore

    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", "django")


@session(python=["3.11"], name="Starlette tests", tags=["tests"])
@gql_core_parametrize
def tests_starlette(session: Session, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install("starlette")  # type: ignore
    _install_gql_core(session, gql_core)
    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", "asgi")


@session(python=["3.11"], name="Test integrations", tags=["tests"])
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
def tests_integrations(session: Session, integration: str, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(integration)  # type: ignore
    _install_gql_core(session, gql_core)
    if integration == "aiohttp":
        session._session.install("pytest-aiohttp")  # type: ignore
    elif integration == "channels":
        session._session.install("pytest-django")  # type: ignore
        session._session.install("daphne")  # type: ignore

    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", integration)


@session(python=PYTHON_VERSIONS, name="Pydantic tests", tags=["tests", "pydantic"])
@with_gql_core_parametrize("pydantic", ["1.10", "2.8.0", "2.9.0"])
def test_pydantic(session: Session, pydantic: str, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"pydantic~={pydantic}")  # type: ignore
    _install_gql_core(session, gql_core)
    session.run(
        "pytest",
        "--cov=.",
        "--cov-append",
        "--cov-report=xml",
        "-m",
        "pydantic",
        "--ignore=tests/cli",
        "--ignore=tests/benchmarks",
    )


@session(python=PYTHON_VERSIONS, name="Type checkers tests", tags=["tests"])
def tests_typecheckers(session: Session) -> None:
    session.run_always("poetry", "install", external=True)

    session.install("pyright")
    session.install("pydantic")
    session.install("mypy")

    session.run(
        "pytest",
        "--cov=.",
        "--cov-append",
        "--cov-report=xml",
        "tests/typecheckers",
        "-vv",
    )


@session(python=PYTHON_VERSIONS, name="CLI tests", tags=["tests"])
def tests_cli(session: Session) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install("uvicorn")  # type: ignore
    session._session.install("starlette")  # type: ignore

    session.run(
        "pytest",
        "--cov=.",
        "--cov-append",
        "--cov-report=xml",
        "tests/cli",
        "-vv",
    )
