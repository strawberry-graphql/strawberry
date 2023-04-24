from __future__ import annotations

from typing import Iterator, Union, TextIO, TYPE_CHECKING
from pathlib import Path

from pyinstrument import Profiler

from strawberry.extensions.base_extension import SchemaExtension


if TYPE_CHECKING:
    from strawberry.types.execution import ExecutionContext


class PyInstrument(SchemaExtension):
    """
    Extension to profile the execution time of resolvers using PyInstrument.
    """

    def __init__(
        self,
        report_path: Path = Path("pyinstrument.html"),
    ) -> None:
        self._report_path = report_path

    def on_operation(self) -> Iterator[None]:
        """
        Called when an operation is started,
        in this case we start the profiler and yield
        then we stop the profiler when the operation is done
        """
        # Start the profiler
        profiler = Profiler()
        profiler.start()

        # Perform the operation
        yield

        # Stop the profiler
        profiler.stop()
        with open(self._report_path, "w", encoding="utf-8") as f:
            f.write(profiler.output_html())
