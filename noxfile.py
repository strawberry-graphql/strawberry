import nox
from nox_poetry import Session, session

PYTHON_VERSIONS = ["3.12", "3.11", "3.10", "3.9", "3.8"]


@session(python=PYTHON_VERSIONS, name="Tests", tags=["tests"])
def tests(session: Session) -> None:
    session.run_always("poetry", "install", external=True)

    markers_to_skip = [
        "starlette",
        "django",
        "starlite",
        "pydantic",
        "sanic",
        "aiohttp",
    ]

    skip_markers = [["-m", f"not {marker}"] for marker in markers_to_skip]
    skip_markers = [item for sublist in skip_markers for item in sublist]

    session.run(
        *[
            "pytest",
            "--cov=strawberry",
            "--cov-append",
            "--cov-report=xml",
            "-n",
            "auto",
            "--showlocals",
            "-vv",
            *skip_markers,
            "--ignore=tests/aiohttp",
            "--ignore=tests/mypy",
            "--ignore=tests/pyright",
        ]
    )


@session(python=["3.11"], name="Django tests", tags=["tests"])
@nox.parametrize("django", ["4.2.0", "4.1.0", "4.0.0", "3.2.0"])
def tests_django(session: Session, django: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"django~={django}")  # type: ignore

    session.run(
        "pytest",
        "--cov=strawberry",
        "--cov-append",
        "--cov-report=xml",
        "-n",
        "auto",
        "--showlocals",
        "-vv",
        "-m",
        "django",
    )


@session(python=["3.11"], name="Aiohttp tests", tags=["tests"])
@nox.parametrize("aiohttp", ["3.8.4"])
def tests_aiohttp(session: Session, aiohttp: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"aiohttp~={aiohttp}")  # type: ignore
    session._session.install("pytest-aiohttp")  # type: ignore

    session.run(
        "pytest",
        "--cov=strawberry",
        "--cov-append",
        "--cov-report=xml",
        "-n",
        "auto",
        "--showlocals",
        "-vv",
        "-m",
        "aiohttp",
    )


@session(python=["3.11"], name="Sanic tests", tags=["tests"])
@nox.parametrize("sanic", ["23.3.0"])
def tests_sanic(session: Session, sanic: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"sanic~={sanic}")  # type: ignore

    session.run(
        "pytest",
        "--cov=strawberry",
        "--cov-append",
        "--cov-report=xml",
        "-n",
        "auto",
        "--showlocals",
        "-vv",
        "-m",
        "sanic",
    )


@session(python=["3.11"], name="Starlette tests", tags=["tests"])
@nox.parametrize("starlette", ["0.28.0", "0.27.0", "0.26.1"])
def tests_starlette(session: Session, starlette: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"starlette=={starlette}")  # type: ignore

    session.run(
        "pytest",
        "--cov=strawberry",
        "--cov-append",
        "--cov-report=xml",
        "-n",
        "auto",
        "--showlocals",
        "-vv",
        "-m",
        "starlette",
    )


@session(python=["3.11"], name="Litestar tests", tags=["tests"])
def tests_litestar(session: Session) -> None:
    session.run_always("poetry", "install", external=True)

    session.run(
        "pytest",
        "--cov=strawberry",
        "--cov-append",
        "--cov-report=xml",
        "-n",
        "auto",
        "--showlocals",
        "-vv",
        "-m",
        "starlite",
    )


@session(python=["3.11"], name="Pydantic tests", tags=["tests"])
# TODO: add pydantic 2.0 here :)
@nox.parametrize("pydantic", ["1.10"])
def test_pydantic(session: Session, pydantic: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"pydantic~={pydantic}")  # type: ignore

    session.run(
        "pytest",
        "--cov=strawberry",
        "--cov-append",
        "--cov-report=xml",
        "-n",
        "auto",
        "--showlocals",
        "-vv",
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
