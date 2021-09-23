Release type: patch

Enhances strawberry.extensions.tracing.opentelemetry to include spans for the Parsing and Validation phases of request handling. These occur before your resovler is called, so now you can see how much time those phases take up!
