from typing import Any

from rich.progress import TaskID


class FakeProgress:
    """A fake progress bar that does nothing.

    This is used when the user has only one file to process."""

    def advance(self, task_id: TaskID) -> None:
        pass

    def add_task(self, *args: Any, **kwargs: Any) -> TaskID:
        return TaskID(0)

    def __enter__(self) -> "FakeProgress":
        return self

    def __exit__(self, *args: object, **kwargs: Any) -> None:
        pass
