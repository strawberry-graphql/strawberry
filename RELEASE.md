---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release speeds up benchmark feedback
    by running CodSpeed checks across parallel CI jobs.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release speeds up benchmark feedback
    by running CodSpeed checks across parallel CI jobs while preserving the
    existing benchmark coverage.
---

This release adds parallel execution to Strawberry's benchmark checks.

CodSpeed benchmarks now run across four parallel CI jobs while preserving the
existing benchmark coverage and simulation mode.
