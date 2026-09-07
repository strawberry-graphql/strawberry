import asyncio
import json

import httpx
import pytest
from fastapi import FastAPI
from pytest_codspeed import BenchmarkFixture

from strawberry.asgi import GraphQL
from strawberry.fastapi import GraphQLRouter

from .api import schema

pytestmark = pytest.mark.benchmark_native


@pytest.mark.parametrize("framework", ["asgi", "fastapi"])
@pytest.mark.parametrize("count", [1, 1000])
def test_http_post(
    benchmark: BenchmarkFixture,
    benchmark_loop: asyncio.AbstractEventLoop,
    framework: str,
    count: int,
    record_property,
):
    if framework == "asgi":
        app = GraphQL(schema)
    else:
        app = FastAPI()
        app.include_router(GraphQLRouter(schema), prefix="/graphql")
    expected = {"data": {"items": [{"name": "Item", "index": i} for i in range(count)]}}
    payload = json.dumps(
        {
            "query": "query ($count: Int!) { items(count: $count) { name index } }",
            "variables": {"count": count},
        }
    ).encode()
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://benchmark"
    )

    async def run():
        return await client.post(
            "/graphql", content=payload, headers={"content-type": "application/json"}
        )

    try:
        result = benchmark(lambda: benchmark_loop.run_until_complete(run()))
        assert result.status_code == 200
        assert result.json() == expected
        # Response bytes are an explicit workload contract, not a latency percentile.
        assert result.content == json.dumps(expected, separators=(",", ":")).encode()
        record_property("response_bytes", len(result.content))
    finally:
        benchmark_loop.run_until_complete(client.aclose())
