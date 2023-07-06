from __future__ import annotations

from pathlib import Path
from typing import Iterator

from pyinstrument import Profiler

from strawberry.extensions.base_extension import SchemaExtension


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
        profiler = Profiler()
        profiler.start()

        yield

        profiler.stop()

        Path(self._report_path, encoding="utf-8").write_text(profiler.output_html())
