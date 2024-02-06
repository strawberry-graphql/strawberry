---
title: Tracing
---

# Tracing

## Apollo

To enable [Apollo tracing](https://github.com/apollographql/apollo-tracing) you
can use the ApolloTracingExtension provided:

```python
from strawberry.extensions.tracing import ApolloTracingExtension

schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension])
```

Note that if you're not running under ASGI you'd need to use the sync version of
ApolloTracingExtension:

```python
from strawberry.extensions.tracing import ApolloTracingExtensionSync

schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtensionSync])
```

## Datadog

In addition to Apollo Tracing we also support tracing with
[Datadog](https://www.datadoghq.com/). using the DatadogTracingExtension.

```python
from strawberry.extensions.tracing import DatadogTracingExtension

schema = strawberry.Schema(query=Query, extensions=[DatadogTracingExtension])
```

Note that if you're not running under ASGI you'd need to use the sync version of
DatadogTracingExtension:

```python
from strawberry.extensions.tracing import DatadogTracingExtensionSync

schema = strawberry.Schema(query=Query, extensions=[DatadogTracingExtensionSync])
```

## Open Telemetry

In addition to Datadog and Apollo Tracing we also support
[opentelemetry](https://opentelemetry.io/), using the OpenTelemetryExtension.

You also need to install the extras for opentelemetry by doing:

```shell
pip install 'strawberry-graphql[opentelemetry]'
```

```python
from strawberry.extensions.tracing import OpenTelemetryExtension

schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])
```

Note that if you're not running under ASGI you'd need to use the sync version of
OpenTelemetryExtension:

```python
from strawberry.extensions.tracing import OpenTelemetryExtensionSync

schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtensionSync])
```

Example Elasticsearch, Kibana, APM, Collector docker-compose to track django and
strawberry tracing metrics

This will spin up:

- an elastic search instance to keep your data
- kibana to visualize data
- the elastic APM Server for processing incoming traces
- a
  [collector binding](https://github.com/open-telemetry/opentelemetry-python/tree/main/exporter/opentelemetry-exporter-otlp)
  to transform the opentelemetry data (more exactly the Opentelementry Line
  Protocol OTLP) to something AMP can read
  ([our APM agent](https://github.com/open-telemetry/opentelemetry-collector))

For more details see the elasticsearch
[docs](https://www.elastic.co/guide/en/apm/get-started/current/open-telemetry-elastic.html)

```yaml
version: "3"

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.16.2
    container_name: elasticsearch
    restart: always
    ulimits:
      memlock:
        soft: -1
        hard: -1
    environment:
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms1024m -Xmx1024m"
      - ELASTIC_PASSWORD=changeme
      - xpack.security.enabled=true
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    healthcheck:
      interval: 10s
      retries: 12
      test:
        curl -s http://localhost:9200/_cluster/health | grep -vq
        '"status":"red"'

  kibana:
    image: docker.elastic.co/kibana/kibana:7.16.2
    container_name: kibana
    environment:
      ELASTICSEARCH_URL: "http://elasticsearch:9200"
      ELASTICSEARCH_HOSTS: '["http://elasticsearch:9200"]'
      ELASTICSEARCH_USERNAME: elastic
      ELASTICSEARCH_PASSWORD: changeme
    restart: always
    depends_on:
      elasticsearch:
        condition: service_healthy
    ports:
      - 127.0.0.1:5601:5601

  apm-server:
    image: docker.elastic.co/apm/apm-server:7.16.2
    container_name: apm-server
    user: apm-server
    restart: always
    command:
      [
        "--strict.perms=false",
        "-e",
        "-E",
        "apm-server.host=0.0.0.0:8200",
        "-E",
        "apm-server.kibana.enabled=true",
        "-E",
        "apm-server.kibana.host=kibana:5601",
        "-E",
        "apm-server.kibana.username=elastic",
        "-E",
        "apm-server.kibana.password=changeme",
        "-E",
        "output.elasticsearch.hosts=['elasticsearch:9200']",
        "-E",
        "output.elasticsearch.enabled=true",
        "-E",
        "output.elasticsearch.username=elastic",
        "-E",
        "output.elasticsearch.password=changeme",
      ]
    depends_on:
      elasticsearch:
        condition: service_healthy
    cap_add: ["CHOWN", "DAC_OVERRIDE", "SETGID", "SETUID"]
    cap_drop: ["ALL"]
    healthcheck:
      interval: 10s
      retries: 12
      test:
        curl --write-out 'HTTP %{http_code}' --fail --silent --output /dev/null
        http://localhost:8200/

  otel-collector:
    image: otel/opentelemetry-collector:0.41.0
    container_name: otel-collector
    restart: always
    command: "--config=/etc/otel-collector-config.yaml"
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml:ro
    depends_on:
      apm-server:
        condition: service_healthy
    ports:
      - 127.0.0.1:4317:4317

volumes:
  elasticsearch-data:
    external: true
```

In the same directory add a `otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:

processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 2000
  batch:

exporters:
  logging:
    loglevel: warn
  otlp/elastic:
    endpoint: "apm-server:8200"
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [logging, otlp/elastic]
      processors: [batch]
    metrics:
      receivers: [otlp]
      exporters: [logging, otlp/elastic]
      processors: [batch]
```

Spin this docker-compose up with (this will take a while, give it a minute):

```shell
docker-compose up --force-recreate --build
```

Example Django Integration

Requirements:

```shell
pip install opentelemetry-api
pip install opentelemetry-sdk
pip install opentelemetry-exporter-otlp
```

in the manage.py

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

resource = Resource(attributes={"service.name": "yourservicename"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

...


def main():
    DjangoInstrumentor().instrument()
    ...
```
