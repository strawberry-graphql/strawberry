# Copy of the Promise library (https://github.com/syrusakbary/promise) with some
# modifications.
#
# Promise is licensed under the terms of the MIT license, reproduced below.
#
# = = = = =
#
# The MIT License (MIT)
#
# Copyright (c) 2016 Syrus Akbary
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from asyncio import Future, sleep

from pytest import mark

from strawberry.promise import Promise, is_thenable


@mark.asyncio
async def test_await():
    assert await Promise.resolve(True)


@mark.asyncio
async def test_promisify_coroutine():
    async def my_coroutine():
        await sleep(0.01)
        return True

    assert await Promise.resolve(my_coroutine())


@mark.asyncio
async def test_coroutine_is_thenable():
    async def my_coroutine():
        await sleep(0.01)
        return True

    assert is_thenable(my_coroutine())


@mark.asyncio
async def test_promisify_future():
    future = Future()
    future.set_result(True)
    assert await Promise.resolve(future)


@mark.asyncio
async def test_await_in_safe_promise():
    async def inner():
        @Promise.safe
        def x():
            promise = Promise.resolve(True).then(lambda x: x)
            return promise

        return await x()

    result = await inner()
    assert result is True
