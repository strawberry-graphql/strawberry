ARG VARIANT=3.13
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

RUN pip3 install pre-commit
