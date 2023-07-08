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
