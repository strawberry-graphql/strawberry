Release type: minor

In this release, the return types of the `get_root_value` and `get_context`
methods were updated to be consistent across all view integrations. Before this
release, the return types used by the ASGI and Django views were too generic.
