import asyncio
from asyncio.base_events import BaseEventLoop
from unittest import mock


class TickEventLoop(BaseEventLoop):
    """A fake event loop that uses a simple counter for the time."""

    _selector = mock.Mock()
    _selector.select.return_value = ()
    _process_events = mock.Mock()

    def __init__(self, *args, **kwargs):
        self._current_tick = 0

        super().__init__(*args, **kwargs)

    def _run_once(self):
        self._current_tick += 1

        return super()._run_once()

    def time(self):
        return self._current_tick


class TickEventLoopPolicy(asyncio.DefaultEventLoopPolicy):  # type:ignore
    def new_event_loop(self):
        return TickEventLoop()
