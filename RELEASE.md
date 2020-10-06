Release type: minor

This releases adds a new extension for OpenTelemetry.

```python
import asyncio

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleExportSpanProcessor,
)

import strawberry
from strawberry.extensions.tracing import OpenTelemetryExtension


trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    SimpleExportSpanProcessor(ConsoleSpanExporter())
)


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    async def user(self, name: str) -> User:
        await asyncio.sleep(0.1)
        return User(name)


schema = strawberry.Schema(Query, extensions=[OpenTelemetryExtension])
```
