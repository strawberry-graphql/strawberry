Release type: minor

Adjust the `strawberry.asdict` function to handle `Some` and `UNSET` values.

If a field has the value `UNSET`, it is not included in the output.
If a field type is `Maybe[T]` and the field is `None`, it is not included in the output.
