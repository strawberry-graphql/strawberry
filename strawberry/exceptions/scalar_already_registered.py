from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from strawberry.exceptions.utils.source_finder import SourceFinder

from .exception import StrawberryException

if TYPE_CHECKING:
    from strawberry.types.scalar import ScalarDefinition

    from .exception_source import ExceptionSource


class ScalarAlreadyRegisteredError(StrawberryException):
    def __init__(
        self,
        scalar_definition: ScalarDefinition,
        other_scalar_definition: ScalarDefinition,
    ) -> None:
        self.scalar_definition = scalar_definition

        scalar_name = scalar_definition.name

        self.message = f"Scalar `{scalar_name}` has already been registered"
        self.rich_message = (
            f"Scalar `[underline]{scalar_name}[/]` has already been registered"
        )
        self.annotation_message = "scalar defined here"
        self.suggestion = (
            "To fix this error you should either rename the scalar, "
            "or reuse the existing one"
        )
        if other_scalar_definition._source_file:
            other_path = Path(other_scalar_definition._source_file)
            other_line = other_scalar_definition._source_line

            self.suggestion += (
                f", defined in [bold white][link=file://{other_path}]"
                f"{other_path.relative_to(Path.cwd())}:{other_line}[/]"
            )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if not all(
            (self.scalar_definition._source_file, self.scalar_definition._source_line)
        ):
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_scalar_call(self.scalar_definition)
