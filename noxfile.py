from nox_poetry import session


@session(python=["3.10", "3.9"])
def tests(session):
    session.run_always("poetry", "install", external=True)
    session.run("pytest")
