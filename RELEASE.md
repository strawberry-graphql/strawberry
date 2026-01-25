Release type: patch

Fix union type resolution to fall back to `is_type_of` for generic unions when
type matching fails. This allows returning domain/ORM objects from generic union
fields without spurious union type errors.
