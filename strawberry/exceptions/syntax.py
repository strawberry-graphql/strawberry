from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Set, Tuple

from pygments.lexers import PythonLexer
from rich.segment import Segment
from rich.syntax import Syntax as RichSyntax

if TYPE_CHECKING:
    from rich.console import Console, ConsoleOptions, RenderResult


class Syntax(RichSyntax):
    def __init__(
        self,
        code: str,
        line_range: Tuple[int, int],
        highlight_lines: Optional[Set[int]] = None,
        line_offset: int = 0,
        line_annotations: Optional[Dict[int, str]] = None,
    ) -> None:
        self.line_offset = line_offset
        self.line_annotations = line_annotations or {}

        super().__init__(
            code=code,
            lexer=PythonLexer(),
            line_numbers=True,
            word_wrap=False,
            theme="ansi_light",
            highlight_lines=highlight_lines,
            line_range=line_range,
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        assert self.line_range

        segments = self._get_syntax(console, options)
        annotations = self.line_annotations.copy()
        current_line = self.line_range[0] or 0

        for segment in segments:
            if segment.text == "\n":
                # 3 = | + space + space
                prefix = " " * (self._numbers_column_width + 3)

                annotation = annotations.pop(current_line, None)

                current_line += 1

                if annotation:
                    yield ""
                    yield prefix + annotation

                    continue

            yield segment

            if segment.text.strip() == str(current_line):
                yield Segment("| ")
