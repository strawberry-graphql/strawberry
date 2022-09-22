Release type: minor

Support retrieving the current resolver's `Info` without relying on arguments.

Instead of adding the `Info` explicitly to the resolver's arguments, it is now possible to retrieve it
anywhere with `strawberry.get_info()`.
