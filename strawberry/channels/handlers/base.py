import asyncio
import contextlib
import warnings
from collections import defaultdict
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    DefaultDict,
    List,
    Optional,
    Sequence,
)
from typing_extensions import Literal, Protocol, TypedDict
from weakref import WeakSet

from channels.consumer import AsyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ChannelsMessage(TypedDict, total=False):
    type: str


class ChannelsLayer(Protocol):  # pragma: no cover
    """Channels layer spec.

    Based on: https://channels.readthedocs.io/en/stable/channel_layer_spec.html
    """

    # Default channels API

    extensions: List[Literal["groups", "flush"]]

    async def send(self, channel: str, message: dict) -> None: ...

    async def receive(self, channel: str) -> dict: ...

    async def new_channel(self, prefix: str = ...) -> str: ...

    # If groups extension is supported

    group_expiry: int

    async def group_add(self, group: str, channel: str) -> None: ...

    async def group_discard(self, group: str, channel: str) -> None: ...

    async def group_send(self, group: str, message: dict) -> None: ...

    # If flush extension is supported

    async def flush(self) -> None: ...


class ChannelsConsumer(AsyncConsumer):
    """Base channels async consumer."""

    channel_name: str
    channel_layer: Optional[ChannelsLayer]
    channel_receive: Callable[[], Awaitable[dict]]

    def __init__(self, *args: str, **kwargs: Any) -> None:
        self.listen_queues: DefaultDict[str, WeakSet[asyncio.Queue]] = defaultdict(
            WeakSet
        )
        super().__init__(*args, **kwargs)

    async def dispatch(self, message: ChannelsMessage) -> None:
        # AsyncConsumer will try to get a function for message["type"] to handle
        # for both http/websocket types and also for layers communication.
        # In case the type isn't one of those, pass it to the listen queue so
        # that it can be consumed by self.channel_listen
        type_ = message.get("type", "")
        if type_ and not type_.startswith(("http.", "websocket.")):
            for queue in self.listen_queues[type_]:
                queue.put_nowait(message)
            return

        await super().dispatch(message)

    async def channel_listen(
        self,
        type: str,
        *,
        timeout: Optional[float] = None,
        groups: Sequence[str] = (),
    ) -> AsyncGenerator[Any, None]:
        """Listen for messages sent to this consumer.

        Utility to listen for channels messages for this consumer inside
        a resolver (usually inside a subscription).

        Args:
            type:
                The type of the message to wait for.
            timeout:
                An optional timeout to wait for each subsequent message
            groups:
                An optional sequence of groups to receive messages from.
                When passing this parameter, the groups will be registered
                using `self.channel_layer.group_add` at the beggining of the
                execution and then discarded using `self.channel_layer.group_discard`
                at the end of the execution.
        """
        warnings.warn("Use listen_to_channel instead", DeprecationWarning, stacklevel=2)
        if self.channel_layer is None:
            raise RuntimeError(
                "Layers integration is required listening for channels.\n"
                "Check https://channels.readthedocs.io/en/stable/topics/channel_layers.html "
                "for more information"
            )

        added_groups = []
        try:
            # This queue will receive incoming messages for this generator instance
            queue: asyncio.Queue = asyncio.Queue()
            # Create a weak reference to the queue. Once we leave the current scope, it
            # will be garbage collected
            self.listen_queues[type].add(queue)

            for group in groups:
                await self.channel_layer.group_add(group, self.channel_name)
                added_groups.append(group)

            while True:
                awaitable = queue.get()
                if timeout is not None:
                    awaitable = asyncio.wait_for(awaitable, timeout)
                try:
                    yield await awaitable
                except asyncio.TimeoutError:
                    # TODO: shall we add log here and maybe in the suppress below?
                    return
        finally:
            for group in added_groups:
                with contextlib.suppress(Exception):
                    await self.channel_layer.group_discard(group, self.channel_name)

    @contextlib.asynccontextmanager
    async def listen_to_channel(
        self,
        type: str,
        *,
        timeout: Optional[float] = None,
        groups: Sequence[str] = (),
    ) -> AsyncGenerator[Any, None]:
        """Listen for messages sent to this consumer.

        Utility to listen for channels messages for this consumer inside
        a resolver (usually inside a subscription).

        Args:
            type:
                The type of the message to wait for.
            timeout:
                An optional timeout to wait for each subsequent message
            groups:
                An optional sequence of groups to receive messages from.
                When passing this parameter, the groups will be registered
                using `self.channel_layer.group_add` at the beggining of the
                execution and then discarded using `self.channel_layer.group_discard`
                at the end of the execution.
        """
        # Code to acquire resource (Channels subscriptions)
        if self.channel_layer is None:
            raise RuntimeError(
                "Layers integration is required listening for channels.\n"
                "Check https://channels.readthedocs.io/en/stable/topics/channel_layers.html "
                "for more information"
            )

        added_groups = []
        # This queue will receive incoming messages for this generator instance
        queue: asyncio.Queue = asyncio.Queue()
        # Create a weak reference to the queue. Once we leave the current scope, it
        # will be garbage collected
        self.listen_queues[type].add(queue)

        # Subscribe to all groups but return generator object to allow user
        # code to run before blocking on incoming messages
        for group in groups:
            await self.channel_layer.group_add(group, self.channel_name)
            added_groups.append(group)
        try:
            yield self._listen_to_channel_generator(queue, timeout)
        finally:
            # Code to release resource (Channels subscriptions)
            for group in added_groups:
                with contextlib.suppress(Exception):
                    await self.channel_layer.group_discard(group, self.channel_name)

    async def _listen_to_channel_generator(
        self, queue: asyncio.Queue, timeout: Optional[float]
    ) -> AsyncGenerator[Any, None]:
        """Generator for listen_to_channel method.

        Seperated to allow user code to be run after subscribing to channels
        and before blocking to wait for incoming channel messages.
        """
        while True:
            awaitable = queue.get()
            if timeout is not None:
                awaitable = asyncio.wait_for(awaitable, timeout)
            try:
                yield await awaitable
            except asyncio.TimeoutError:
                # TODO: shall we add log here and maybe in the suppress below?
                return


class ChannelsWSConsumer(ChannelsConsumer, AsyncJsonWebsocketConsumer):
    """Base channels websocket async consumer."""


__all__ = ["ChannelsConsumer", "ChannelsWSConsumer"]
