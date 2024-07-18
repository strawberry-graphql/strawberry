import nox
from nox_poetry import Session, session

nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True

PYTHON_VERSIONS = ["3.12", "3.11", "3.10", "3.9", "3.8"]
GQL_CORE_VERSIONS = [
    "graphql-core~=3.2.0",
    "https://github.com/graphql-python/graphql-core/archive/876aef67b6f1e1f21b3b5db94c7ff03726cb6bdf.zip",
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
    "starlite",
    "litestar",
    "pydantic",
]


def _install_package(session: Session, package: str) -> None:
    session._session.install(package)  # type: ignore


gql_core_parametrize = nox.parametrize("gql_core", GQL_CORE_VERSIONS)


@session(python=PYTHON_VERSIONS, name="Tests", tags=["tests"])
@gql_core_parametrize
def tests(session: Session, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)
    _install_package(session, gql_core)
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


@session(python=["3.11", "3.12"], name="Django tests", tags=["tests"])
@nox.parametrize("django", ["4.2.0", "4.1.0", "4.0.0", "3.2.0"])
@gql_core_parametrize
def tests_django(session: Session, django: str, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)
    _install_package(session, gql_core)
    session._session.install(f"django~={django}")  # type: ignore
    session._session.install("pytest-django")  # type: ignore

    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", "django")


@session(python=["3.11"], name="Starlette tests", tags=["tests"])
@gql_core_parametrize
@nox.parametrize("starlette", ["0.28.0", "0.27.0", "0.26.1"])
def tests_starlette(session: Session, starlette: str, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"starlette=={starlette}")  # type: ignore
    _install_package(session, gql_core)
    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", "asgi")


@session(python=["3.11"], name="Test integrations", tags=["tests"])
@gql_core_parametrize
@nox.parametrize(
    "integration",
    [
        "aiohttp",
        "chalice",
        "channels",
        "fastapi",
        "flask",
        "quart",
        "sanic",
        "starlite",
        "litestar",
    ],
)
def tests_integrations(session: Session, integration: str, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(integration)  # type: ignore
    _install_package(session, gql_core)
    if integration == "aiohttp":
        session._session.install("pytest-aiohttp")  # type: ignore
    elif integration == "channels":
        session._session.install("pytest-django")  # type: ignore
        session._session.install("daphne")  # type: ignore
    elif integration == "starlite":
        session._session.install("pydantic<2.0")  # type: ignore

    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", integration)


@session(python=PYTHON_VERSIONS, name="Pydantic tests", tags=["tests", "pydantic"])
@gql_core_parametrize
@nox.parametrize("pydantic", ["1.10", "2.7.0"])
def test_pydantic(session: Session, pydantic: str, gql_core: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"pydantic~={pydantic}")  # type: ignore
    _install_package(session, gql_core)
    session.run(
        "pytest",
        "--cov=.",
        "--cov-append",
        "--cov-report=xml",
        "-m",
        "pydantic",
        "--ignore=tests/cli",
    )


@session(python=PYTHON_VERSIONS, name="Type checkers tests", tags=["tests"])
def tests_typecheckers(session: Session) -> None:
    session.run_always("poetry", "install", external=True)

    session.install("pyright")
    session.install("pydantic")
    session.install("git+https://github.com/python/mypy.git#master")

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


@session(name="Mypy", tags=["lint"])
def mypy(session: Session) -> None:
    session.run_always("poetry", "install", "--with", "integrations", external=True)
    session.install("mypy")

    session.run("mypy", "--config-file", "mypy.ini")
