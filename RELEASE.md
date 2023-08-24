Release type: minor

`strawberry codegen` previously choked for inputs that used the
`strawberry.UNSET` sentinal singleton value as a default.  The intent
here is to say that if a variable is not part of the request payload,
then the `UNSET` default value will not be modified and the service
code can then treat an unset value differently from a default value,
etc.

For codegen, we treat the `UNSET` default value as a `GraphQLNullValue`.
The `.value` property is the `UNSET` object in this case (instead of
the usual `None`).  In the built-in python code generator, this causes
the client to generate an object with a `None` default.  Custom client
generators can sniff at this value and update their behavior.
