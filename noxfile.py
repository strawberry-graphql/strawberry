from nox_poetry import Session, session


@session(python=["3.11", "3.10", "3.9", "3.8", "3.7"])
def tests(session: Session) -> None:
    session.run_always("poetry", "install", external=True)
    session.run("pytest")
