from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pyinstrument import Profiler

from strawberry.extensions.base_extension import SchemaExtension

if TYPE_CHECKING:
    from collections.abc import Iterator


class PyInstrument(SchemaExtension):
    """Extension to profile the execution time of resolvers using PyInstrument."""

    def __init__(
        self,
        report_path: Path = Path("pyinstrument.html"),
    ) -> None:
        self._report_path = report_path

    def on_operation(self) -> Iterator[None]:
        profiler = Profiler()
        profiler.start()

        yield

        profiler.stop()

        self._report_path.write_text(profiler.output_html())


__all__ = ["PyInstrument"]
