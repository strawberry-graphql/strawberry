Release type: patch

Improve development environment with below changes:

- Set Python version to 3.10 in devcontainer to support Litestar dependency requirements.
    - Tests fail otherwise.
- Migrate to newer `mcr.microsoft.com/devcontainers/python` base image.
- Add integration dependencies to post-install script.
    - Tests fail without & is now inline with documentation: `$ poetry install --with integrations`.
- Correct devcontainer.json settings structure.

Changes only impact the development environment.
