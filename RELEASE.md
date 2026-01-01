Release type: patch

Fixed two bugs where using `strawberry.Maybe` wrapped in `Annotated` or using an explicit field definition would raise a `TypeError` about "missing 1 required keyword-only argument", even though a `Maybe` field should allow `None` in all cases.

This fix addresses this via custom handling for annotations wrapped with `Annotated` and handling custom `field` with no `default` and no `default_factory` as possible to be `None`.
