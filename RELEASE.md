---
release type: patch
social_messages:
  x: >-
    {project_name} {version} fixes a bug where Datadog spans could be left open when an operation raised an exception.
  linkedin: >-
    {project_name} {version} makes sure the Datadog extension always closes spans.
---

This release fixes an issue with the Datadog extension.

Strawberry now makes sure that the Datadog extension always closes spans,
also in the case of exceptions.
