---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release adds explicit warmup to the
    permission benchmarks. https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds explicit warmup to the
    permission benchmarks while retaining complete request execution and
    allocation costs in the measurements.
---

This release adds explicit warmup to the permission and handled-error benchmarks.

Each benchmark warms the same request ten times before measurement. Each
measured callback continues to include parsing, validation,
permission checks, exception handling and allocation costs.
