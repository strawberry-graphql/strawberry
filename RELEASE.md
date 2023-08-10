Release type: minor

Add support for extra colons in the `GlobalID` string.

Before, the string `SomeType:some:value` would produce raise an error saying that
it was expected the string to be splited in 2 parts when doing `.split(":")`.

Now we are using `.split(":", 1)`, meaning that the example above will consider
`SomeType` to be the type name, and `some:value` to be the node_id.
