Release type: patch

This release fixes an issue on `relay.ListConnection` where async iterables that returns
non async iterable objects after being sliced where producing errors.

This should fix an issue with async strawberry-graphql-django when returning already
prefetched QuerySets.
