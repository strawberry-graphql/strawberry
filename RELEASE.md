Release type: minor

Added extra validation that types used in a schema are unique.
Strawberry starts to throw an exception `DuplicatedTypeName` when two types defined in a schema have the same name.
