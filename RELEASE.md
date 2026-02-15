Release type: patch

Fix `Annotated[Union[A, B], strawberry.union("Name")]` raising `TypeError` when
used as a type parameter in a generic subclass (e.g., `class Items(Listing[ItemResponse])`).
