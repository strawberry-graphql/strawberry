Release type: patch

In this release, we updated the type hints for `subscription_protocols` across
all HTTP view integrations. It's now consistently defined as `Sequence[str]`,
the minimum type required by Strawberry.
