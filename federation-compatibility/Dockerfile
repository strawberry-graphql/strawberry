FROM python:3.14-slim
WORKDIR /web

RUN apt update && apt install -y gcc g++ python3-dev

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install dependencies first using bind mounts so the layer is cached
# independently from the source code.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --frozen --no-install-project

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY strawberry ./strawberry
COPY federation-compatibility/schema.py ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

EXPOSE 4001

CMD ["uv", "run", "strawberry", "dev", "-p", "4001", "-h", "0.0.0.0", "schema:schema"]
