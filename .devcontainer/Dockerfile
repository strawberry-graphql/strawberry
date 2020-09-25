ARG VARIANT=3.8
FROM mcr.microsoft.com/vscode/devcontainers/python:${VARIANT}

RUN pip3 install poetry pre-commit
RUN poetry config virtualenvs.in-project true
