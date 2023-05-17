Release type: patch

This release adds a method on the DatadogTracingExtension class called `create_span` that can be overridden to create a custom span or add additional tags to the span.

```python
from ddtrace import Span

from strawberry.extensions.tracing import DatadogTracingExtension, LifeCycleStep


class DataDogExtension(DatadogTracingExtension):
    def create_span(
        self,
        lifecycle_step: LifeCycleStep,
        name: str,
        **kwargs,
    ) -> Span:
        span = super().create_span(lifecycle_step, name, **kwargs)
        if lifecycle_step == LifeCycleStep.OPERATION:
            span.set_tag("graphql.query", self.execution_context.query)
        return span
```
