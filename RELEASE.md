Release type: minor

Add `is_auto` utility for checking if a type is `strawberry.auto`,
considering the possibility of it being a `StrawberryAnnotation` or
even being used inside `Annotated`.
