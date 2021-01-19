---
title: Subscriptions
---

# Subscriptions

In GraphQL you can use subscriptions to stream data from a server. To enable
this with Strawberry your server must support ASGI and websockets.

This is how you define a subscription-capable resolver:

```python
import asyncio

import strawberry

@strawberry.type
class Query:
    @strawberry.field
    def hello() -> str:
        return "world"

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> int:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)

schema = strawberry.Schema(query=Query, subscription=Subscription)
```

Like queries and mutations, subscriptions are defined in a class and passed
to the Schema function. Here we create a rudimentary counting function which
counts from 0 to the target sleeping between each loop iteration.

We would send the following GraphQL document to our server to subscribe to this
data stream:

```graphql
subscription {
  count(target: 5)
}
```

In this example, the data looks like this as it passes over the websocket:

![](../images/subscriptions-count-websocket.png)

This is a very short example of what is possible. Like with queries and
mutations the subscription can return any GraphQL type, not only scalars as
demonstrated here.

## Advanced Subscription Patterns

Typically a GraphQL subscription is streaming something more interesting back.
With that in mind your subscription function can return one of:

- `AsyncIterator`, or
- `AsyncGenerator`

Both of these types are documented in [PEP-525][pep-525]. Anything yielded from
these types of resolvers will be shipped across the websocket. Care needs to be
taken to ensure the returned values conform to the GraphQL schema.

The benefit of an AsyncGenerator, over an interator, is that the complex
business logic can be broken out into a seperate module within your codebase.
Allowing you to keep the resolver logic succinct.

The following example is similar to the one above, except it returns an
AsyncGenerator to the ASGI server which is responsible for streaming
subscription results until the Generator exits.

```python
import asyncio
import asyncio.subprocess as subprocess
from asyncio import streams
from typing import Any, AsyncGenerator, AsyncIterator, Coroutine, Optional


async def wait_for_call(coro: Coroutine[Any, Any, bytes]) -> Optional[bytes]:
    """
    wait_for_call calls the the supplied coroutine in a wait_for block.

    This mitigates cases where the coroutine doesn't yield until it has
    completed its task. In this case, reading a line from a StreamReader; if
    there are no `\n` line chars in the stream the function will never exit
    """
    try:
        return await asyncio.wait_for(coro(), timeout=0.1)
    except asyncio.TimeoutError:
        pass


async def lines(stream: streams.StreamReader) -> AsyncIterator[str]:
    """
    lines reads all lines from the provided stream, decoding them as UTF-8
    strings.
    """
    while True:
        b = await wait_for_call(stream.readline)
        if b:
            yield b.decode("UTF-8").rstrip()
        else:
            break


async def exec_proc(target: int) -> subprocess.Process:
    """
    exec_proc starts a sub process and returns the handle to it.
    """
    return await asyncio.create_subprocess_exec(
        "/bin/bash",
        "-c",
        f"for ((i = 0 ; i < {target} ; i++)); do echo $i; sleep 0.2; done",
        stdout=subprocess.PIPE,
    )


async def tail(proc: subprocess.Process) -> AsyncGenerator[str, None]:
    """
    tail reads from stdout until the process finishes
    """
    # Note: race conditions are possible here since we're in a subprocess. In
    # this case the process can finish between the loop predicate and the call
    # to read a line from stdout. This is a good example of why you need to
    # be defensive by using asyncio.wait_for in wait_for_call().
    while proc.returncode is None:
        async for l in lines(proc.stdout):
            yield l
    else:
        # read anything left on the pipe after the process has finished
        async for l in lines(proc.stdout):
            yield l

@strawberry.type
class Query:
    @strawberry.field
    def hello() -> str:
        return "world"

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def run_command(self, target: int = 100) -> AsyncGenerator[str, None]:
        proc = await exec_proc(target)
        return tail(proc)


schema = strawberry.Schema(query=Query, subscription=Subscription)
```

[pep-525]: https://www.python.org/dev/peps/pep-0525/
