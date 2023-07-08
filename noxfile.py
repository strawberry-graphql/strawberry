import nox
from nox_poetry import Session, session


@session(python=["3.11", "3.10", "3.9", "3.8", "3.7"])
def tests(session: Session) -> None:
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
        "not starlette",
        "-m",
        "not django",
        "-m",
        "not starlite",
        "--ignore=tests/mypy",
        "--ignore=tests/pyright",
    )


@session(python=["3.11"])
@nox.parametrize("django", ["4.2", "4.1", "4.0", "3.2"])
def test_django(session: Session, django: str) -> None:
    session.run_always("poetry", "install", external=True)

    session._session.install(f"django=={django}")  # type: ignore

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


@session(python=["3.11"])
@nox.parametrize("starlette", ["0.28.0", "0.27.0", "0.26.1"])
def test_starlette(session: Session, starlette: str) -> None:
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


@session(python=["3.11"])
def test_litestar(session: Session) -> None:
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
