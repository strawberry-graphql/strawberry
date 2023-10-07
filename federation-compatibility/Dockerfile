FROM python:3.10-slim
WORKDIR /web

RUN apt update && apt install -y gcc python3-dev
RUN pip install poetry

COPY strawberry ./strawberry
COPY pyproject.toml ./
COPY poetry.lock ./
COPY README.md ./

RUN poetry install --with integrations

COPY federation-compatibility/schema.py ./

EXPOSE 4001

CMD poetry run strawberry server -p 4001 -h 0.0.0.0 schema:schema
