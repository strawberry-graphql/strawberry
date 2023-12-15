from strawberry.extensions import SchemaExtension


class APQExtension(SchemaExtension):
    def on_execute(
        self,
    ):  # pragma: no cover # pyright: ignore
        """Called before and after the execution step"""
        yield None
