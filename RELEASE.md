Release type: minor

This release adds a safety check on `strawberry.type`, `strawberry.input` and
`strawberry.interface` decorators. When you try to use them with an object that is not a
class, you will get a nice error message:
`strawberry.type can only be used with classes`
