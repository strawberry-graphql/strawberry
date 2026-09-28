import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True
nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.15", "3.14", "3.13", "3.12", "3.11", "3.10"]

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


@nox.session(python=PYTHON_VERSIONS, name="Tests", tags=["tests"])
def tests(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
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
@nox.parametrize("django", ["6.1.0", "6.0.8", "5.2.17"])
def tests_django(session: nox.Session, django: str) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install(f"django~={django}")
    session.install("pytest-django")

    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", "django")


@nox.session(python=["3.11"], name="Starlette tests", tags=["tests"])
def tests_starlette(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install("starlette")
    session.run("pytest", *COMMON_PYTEST_OPTIONS, "-m", "asgi")


@nox.session(python=["3.11"], name="Test integrations", tags=["tests"])
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
        "litestar",
    ],
)
def tests_integrations(session: nox.Session, integration: str) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install(integration)
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
def test_pydantic(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install("pydantic~=1.10")
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
def test_pydantic_v2(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-group=integrations",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.install("pydantic>=2.2")
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
