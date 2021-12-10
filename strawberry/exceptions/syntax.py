import textwrap
from typing import Dict, List, Optional, Set, Union

from pygments.lexers import PythonLexer
from pygments.token import Comment
from rich._loop import loop_first
from rich.console import Console, ConsoleOptions, RenderResult
from rich.containers import Lines
from rich.segment import Segment
from rich.style import Style
from rich.syntax import Syntax as RichSyntax
from rich.text import Text


class Syntax(RichSyntax):
    def __init__(
        self,
        code: str,
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
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        transparent_background = self._get_base_style().transparent_background

        numbers_column_width = len(str(self.line_offset + self.code.count("\n"))) + 2

        code_width = (
            (
                (options.max_width - numbers_column_width - 1)
                if self.line_numbers
                else options.max_width
            )
            if self.code_width is None
            else self.code_width
        )

        ends_on_nl = self.code.endswith("\n")
        code = self.code if ends_on_nl else self.code + "\n"
        code = textwrap.dedent(code) if self.dedent else code
        code = code.expandtabs(self.tab_size)
        text = self.highlight(code, self.line_range)

        (
            background_style,
            number_style,
            highlight_number_style,
        ) = self._get_number_styles(console)

        lines: Union[List[Text], Lines] = text.split("\n", allow_blank=ends_on_nl)

        if self.indent_guides and not options.ascii_only:
            style = (
                self._get_base_style()
                + self._theme.get_style_for_token(Comment)
                + Style(dim=True)
                + self.background_style
            )
            lines = (
                Text("\n")
                .join(lines)
                .with_indent_guides(self.tab_size, style=style)
                .split("\n", allow_blank=True)
            )

        render_options = options.update(width=code_width)

        highlight_line = self.highlight_lines.__contains__
        _Segment = Segment
        padding = _Segment(" " * numbers_column_width + " ", background_style)
        new_line = _Segment("\n")

        line_pointer = "> " if options.legacy_windows else "❱ "

        for line_no, line in enumerate(lines, 1 + self.line_offset):
            if self.word_wrap:
                wrapped_lines = console.render_lines(
                    line,
                    render_options.update(height=None),
                    style=background_style,
                    pad=not transparent_background,
                )

            else:
                segments = list(line.render(console, end=""))
                if options.no_wrap:
                    wrapped_lines = [segments]
                else:
                    wrapped_lines = [
                        _Segment.adjust_line_length(
                            segments,
                            render_options.max_width,
                            style=background_style,
                            pad=not transparent_background,
                        )
                    ]
            for first, wrapped_line in loop_first(wrapped_lines):
                if first:
                    line_column = str(line_no).rjust(numbers_column_width - 2) + " "

                    if highlight_line(line_no):
                        yield _Segment(line_pointer, Style(color="red"))
                        yield _Segment(line_column, highlight_number_style)
                    else:
                        yield _Segment("  ", highlight_number_style)
                        yield _Segment(line_column, number_style)

                    yield _Segment("| ")

                else:
                    yield padding
                yield from wrapped_line
                yield new_line

                if line_no in self.line_annotations:
                    yield padding
                    # yield _Segment("  ", highlight_number_style)
                    yield _Segment("| ")
                    yield self.line_annotations[line_no]
                    # yield new_line
