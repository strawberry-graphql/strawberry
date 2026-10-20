# Strawberry installed from source with the dev and integrations dependency groups, the way contributors set it up
# with `uv sync`. The integrations group pulls in every web framework Strawberry ships a view for, so all HTTP and
# WebSocket integrations can be exercised offline.
FROM python:3.15-bookworm
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /uvx /usr/local/bin/

# scanner contract: the checkout lives inside the image, at /src
COPY . /src
WORKDIR /src

# The virtual environment lives outside the checkout and is put on PATH, so python and pytest work in every shell
# without going through `uv run` (which would try to resolve and sync again, and the scan has no network).
# codeflash is a performance tool that is not needed here, and its z3-solver dependency has no wheel on every platform.
RUN uv sync --frozen \
      --no-install-package codeflash \
      --no-install-package crosshair-tool \
      --no-install-package codeflash-benchmark \
      --no-install-package z3-solver
ENV PATH=/opt/venv/bin:$PATH \
    UV_OFFLINE=1 \
    UV_FROZEN=1

# pyright fetches a Node.js runtime on first use; do it now because the scan has no network.
RUN pyright --version

# Run the test suite so you know the image works, but do not let a failing test abort the build.
RUN python -m pytest tests -q -n auto --ignore=tests/benchmarks || echo "WARNING: pytest reported failures"
