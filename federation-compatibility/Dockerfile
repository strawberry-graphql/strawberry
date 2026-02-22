FROM python:3.14-slim
WORKDIR /web

RUN apt update && apt install -y gcc g++ python3-dev
RUN pip install uv

COPY strawberry ./strawberry
COPY pyproject.toml ./
COPY uv.lock ./
COPY README.md ./

RUN uv sync

COPY federation-compatibility/schema.py ./

EXPOSE 4001

CMD ["uv", "run", "strawberry", "dev", "-p", "4001", "-h", "0.0.0.0", "schema:schema"]
