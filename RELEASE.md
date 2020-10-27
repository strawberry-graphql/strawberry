Release type: minor

Register UUID's as a custom scalar type instead of the ID type.

⚠️ This is a potential breaking change because inputs of type UUID are now parsed as instances of uuid.UUID instead of strings as they were before.
