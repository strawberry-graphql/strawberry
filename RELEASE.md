Release type: patch

This release fixes a couple of more issues with codegen:

1. Adds support for boolean values in input fields
2. Changes how we unwrap types in order to add full support for LazyTypes, Optionals and Lists
3. Improve also how we generate types for unions, now we don't generate a Union type if the selection is for only one type
