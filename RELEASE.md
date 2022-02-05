Release type: minor

Add better support for custom Pydantic conversion logic and standardize the
behavior when not using `strawberry.auto` as the type.

See https://strawberry.rocks/docs/integrations/pydantic#custom-conversion-logic for details and examples.

Note that this release fixes a bug related to Pydantic aliases in schema
generation. If you have a field with the same name as an aliased Pydantic field
but with a different type than `strawberry.auto`, the generated field will now
use the alias name. This may cause schema changes on upgrade in these cases, so
care should be taken. An upcoming release will add an option to disable the
Pydantic alias behavior at the model level.
