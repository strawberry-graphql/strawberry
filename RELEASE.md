Release type: minor

Added support for Apollo Federation inline tracing (FTV1) format.

When a request includes the `apollo-federation-include-trace: ftv1` header, Strawberry now records resolver timing information and includes it in the response under `extensions.ftv1` as a base64-encoded protobuf message, following the Apollo Federation trace format.
