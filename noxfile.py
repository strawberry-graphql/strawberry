import nox
from nox_poetry import Session, session

PYTHON_VERSIONS = ["3.11", "3.10", "3.9", "3.8", "3.7"]


PYTEST_OPTIONS = [
    "--cov=strawberry",
    "--cov-append",
    "--cov-report=xml",
    "-n",
    "auto",
    "--showlocals",
    "-vv",
]

INTEGRATIONS = [
    "asgi",
    "aiohttp",
    "chalice",
    "channels",
    "django",
    "fastapi",
    "flask",
    "sanic",
    "starlette",
    "starlite",
    "pydantic",
]


@session(python=PYTHON_VERSIONS, name="Tests", tags=["tests"])
def tests(session: Session) -> None:
    session.run_always("poetry", "install", external=True)

    markers = (
        ["-m", f"not {integration}", f"--ignore=tests/{integration}"]
        for integration in INTEGRATIONS
    )
    markers = [item for sublist in markers for item in sublist]

    session.run(
        "pytest",
        *PYTEST_OPTIONS,
        *markers,
        "--ignore=tests/mypy",
        "--ignore=tests/pyright",
        # TODO: reintroduce this
        "--ignore=tests/cli",
        "--ignore=tests/experimental/pydantic",
        "--ignore=tests/websockets",
    )


@session(python=["3.11"], tags=["tests"])
@nox.parametrize("django", ["4.2.0", "4.1.0", "4.0.0", "3.2.0"])
def tests_django(session: Session, django: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"django~={django}")  # type: ignore
    session._session.install("pytest-django")  # type: ignore

    session.run(
        "pytest",
        *PYTEST_OPTIONS,
        "-m",
        "django",
    )


@session(python=["3.11"], name="Starlette tests", tags=["tests"])
@nox.parametrize("starlette", ["0.28.0", "0.27.0", "0.26.1"])
def tests_starlette(session: Session, starlette: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"starlette=={starlette}")  # type: ignore

    session.run(
        "pytest",
        *PYTEST_OPTIONS,
        "-m",
        "starlette",
    )


@session(python=["3.11"], name="Test integrations", tags=["tests"])
@nox.parametrize(
    "integration",
    [
        "aiohttp",
        "chalice",
        "channels",
        "fastapi",
        "flask",
        "sanic",
        "starlite",
    ],
)
def tests_integrations(session: Session, integration: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(integration)  # type: ignore

    if integration == "aiohttp":
        session._session.install("pytest-aiohttp")  # type: ignore
    elif integration == "flask":
        session._session.install("pytest-flask")  # type: ignore

    session.run(
        "pytest",
        *PYTEST_OPTIONS,
        "-m",
        integration,
    )


@session(python=["3.11"], name="Pydantic tests", tags=["tests"])
# TODO: add pydantic 2.0 here :)
@nox.parametrize("pydantic", ["1.10"])
def test_pydantic(session: Session, pydantic: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"pydantic~={pydantic}")  # type: ignore

    session.run(
        "pytest",
        *PYTEST_OPTIONS,
        "-m",
        "pydantic",
    )


@session(python=PYTHON_VERSIONS, name="Mypy tests")
def tests_mypy(session: Session) -> None:
    session.run_always("poetry", "install", external=True)

    session.run(
        "pytest",
        "--cov=strawberry",
        "--cov-append",
        "--cov-report=xml",
        "tests/mypy",
        "-vv",
    )


@session(python=PYTHON_VERSIONS, name="Pyright tests", tags=["tests"])
def tests_pyright(session: Session) -> None:
    session.run_always("poetry", "install", external=True)
    session.install("pyright")

    session.run(
        "pytest",
        "--cov=strawberry",
        "--cov-append",
        "--cov-report=xml",
        "tests/pyright",
        "-vv",
    )


@session(name="Mypy", tags=["lint"])
def mypy(session: Session) -> None:
    session.run_always("poetry", "install", external=True)

    session.run("mypy", "--config-file", "mypy.ini")
