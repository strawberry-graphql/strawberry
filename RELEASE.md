Release type: minor

The common `node: Node` used to resolve relay nodes means we will be relying on
is_type_of to check if the returned object is in fact a subclass of the Node
interface.

However, integrations such as Django, SQLAlchemy and Pydantic will not return
the type itself, but instead an alike object that is later resolved to the
expected type.

In case there are more than one possible type defined for that model that is
being returned, the first one that replies True to `is_type_of` check would be
used in the resolution, meaning that when asking for `"PublicUser:123"`,
strawberry could end up returning `"User:123"`, which can lead to security
issues (such as data leakage).

In here we are introducing a new `strawberry.cast`, which will be used to mark
an object with the already known type by us, and when asking for is_type_of that
mark will be used to check instead, ensuring we will return the correct type.

That `cast` is already in place for the relay node resolution and pydantic.
