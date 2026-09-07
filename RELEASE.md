---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Strawberry's benchmark suite now verifies
    complete results and covers schema construction, caching, Federation, Relay,
    and HTTP responses. https://strawberry.rocks/release/{version}
  linkedin: >-
    Strawberry's benchmark suite now checks complete GraphQL results, controls
    cache state and async timing boundaries, and covers schema construction,
    Federation, Relay, and HTTP responses. Scheduled memory measurements and
    recorded environments make performance changes easier to investigate.
---

This release adds broader, correctness-checked performance benchmarks and
reproducible measurement metadata.

The suite now verifies result sizes and subscription event counts, separates
async loop setup from steady-state execution, explicitly controls cache hits and
misses, and covers schema construction, inputs/scalars, DataLoader cache behavior,
Federation, Relay, permissions, handled exceptions, and ASGI/FastAPI responses.
Changed workloads start new benchmark series. CI retains CPU regression checks,
adds scheduled allocation measurements, and separates large stress workloads from
pull-request checks. This changes benchmark coverage, not application behavior.
