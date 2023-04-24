from typing import Iterator, List, Type

from strawberry.extensions.base_extension import SchemaExtension

from pyinstrument import Profiler

# if TYPE_CHECKING:
#    from graphql import ASTValidationRule


class PyInstrument(SchemaExtension):
    """
    Extension to profile the execution time of resolvers using PyInstrument.
    """

    def __init__(self, report_path: str):
        self.report_path = report_path

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
        with open(self.report_path, "w", encoding="utf-8") as f:
            profiler.output_html(f)
