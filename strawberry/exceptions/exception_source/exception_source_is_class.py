import inspect
from pathlib import Path
from typing import Optional, Type

from backports.cached_property import cached_property

from ..utils.getsource import getsourcelines
from .exception_source import ExceptionSource


class ExceptionSourceIsClass:
    cls: Type

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None

        source_file = inspect.getsourcefile(self.cls)

        if source_file is None:
            return None

        source_lines, line = getsourcelines(self.cls)
        path = Path(source_file)

        return ExceptionSource(
            path=path,
            code=path.read_text(),
            start_line=line,
            error_line=line,
            end_line=line,
            error_column=0,
            error_column_end=0,
        )
