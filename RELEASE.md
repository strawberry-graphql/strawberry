Release type: patch

Improve resolving performance by avoiding extra calls for basic fields.

This change improves performance of resolving a query by skipping `Info`
creation and permission checking for fields that don't have a resolver
or permission classes. In local benchmarks it improves performance of large
results by ~14%.
