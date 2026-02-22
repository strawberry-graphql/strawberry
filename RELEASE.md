Release type: patch

`strawberry.asdict` now correctly handles `Some` and `UNSET` values.
`Some(value)` is unwrapped to its inner value, and fields set to `UNSET`
are excluded from the resulting dictionary.
