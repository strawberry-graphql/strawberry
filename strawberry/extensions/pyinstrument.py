from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from pyinstrument import Profiler

from strawberry.extensions.base_extension import SchemaExtension

if TYPE_CHECKING:
    from strawberry.types.execution import ExecutionContext


class PyInstrument(SchemaExtension):
    """Extension to profile the execution time of resolvers using PyInstrument."""

    def __init__(
        self,
        report_path: Path = Path("pyinstrument.html"),
    ) -> None:
        self._report_path = report_path

    def on_operation(self, execution_context: ExecutionContext) -> Iterator[None]:
        profiler = Profiler()
        profiler.start()

        yield

        profiler.stop()

        Path(self._report_path, encoding="utf-8").write_text(profiler.output_html())


__all__ = ["PyInstrument"]
