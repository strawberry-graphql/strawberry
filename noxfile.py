# type: ignore

import nox


@nox.session(python=["3.7", "3.8", "3.9", "3.10", "3.11"], tags=["test"])
def tests(session):
    session.run("poetry", "install", external=True, silent=True)
    session.run(
        "pytest",
        "-m",
        "not django",
        "-m",
        "not starlette",
        "--ignore=tests/mypy",
        "--ignore=tests/pyright",
    )
    session.notify("coverage")


@nox.session(tags=["test"])
@nox.parametrize("django", ["4.1", "4.0", "3.2"])
def test_django(session, django):
    session.run("poetry", "install", external=True, silent=True)
    session.install(f"django=={django}")
    session.run("pytest", "-m", "django")
    session.notify("coverage")


@nox.session(tags=["test"])
@nox.parametrize(
    "starlette,fastapi",
    [
        ("0.17.1", "<0.85.0"),
        ("0.18.0", "<0.85.0"),
        ("0.19.1", "<0.85.0"),
        ("0.20.4", ">=0.85.0"),
        ("0.21.0", ">=0.85.0"),
    ],
)
def test_starlette(session, starlette, fastapi):
    session.run("poetry", "install", external=True, silent=True)
    session.install(f"starlette=={starlette}")
    session.install(f"fastapi{fastapi}")
    session.run("pytest", "-m", "starlette")
    session.notify("coverage")


# TODO: add 3.11 when supported by mypy
@nox.session(python=["3.7", "3.8", "3.9", "3.10"], tags=["test", "type-checkers"])
def test_mypy(session):
    session.run("poetry", "install", external=True, silent=True)
    session.run("pytest", "tests/mypy")
    session.notify("coverage")


@nox.session(python=["3.7", "3.8", "3.9", "3.10"], tags=["test", "type-checkers"])
def test_pyright(session):
    session.run("poetry", "install", external=True, silent=True)
    session.run("pytest", "tests/pyright")
    session.notify("coverage")


@nox.session
def coverage(session):
    session.install("coverage")
    session.run("coverage")
