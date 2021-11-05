Release type: patch

This releases fixes an issue where you were not allowed
to return a non-strawberry type for fields that return
and interface. Now this works as long as each type
implementing the interface implements an `is_type_of`
classmethod. Previous automatic duck typing on types
that implement an interface now requires explicit
resolution using this classmethod.
