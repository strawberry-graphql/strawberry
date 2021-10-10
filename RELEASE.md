Release type: patch

Fix bug where errors thrown in the on_parse_* extension hooks were being
swallowed instead of being propagated.
