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

from collections.abc import Iterable
from functools import partial
from types import TracebackType
from typing import Any, Collection, Optional, Type, Union


if False:
    from .promise import Promise


class PromiseList(object):

    __slots__ = ("_values", "_length", "_total_resolved", "promise", "_promise_class")

    def __init__(self, values, promise_class):
        # type: (Union[Collection, Promise[Collection]], Type[Promise]) -> None
        self._promise_class = promise_class
        self.promise = self._promise_class()

        self._length = 0
        self._total_resolved = 0
        self._values = None  # type: Optional[Collection]
        Promise = self._promise_class
        if Promise.is_thenable(values):
            values_as_promise = Promise._try_convert_to_promise(
                values
            )._target()  # type: ignore
            self._init_promise(values_as_promise)
        else:
            self._init(values)  # type: ignore

    def __len__(self):
        # type: () -> int
        return self._length

    def _init_promise(self, values):
        # type: (Promise[Collection]) -> None
        if values.is_fulfilled:
            values = values._value()
        elif values.is_rejected:
            self._reject(values._reason())
            return

        self.promise._is_async_guaranteed = True
        values._then(self._init, self._reject)
        return

    def _init(self, values):
        # type: (Collection) -> None
        self._values = values
        if not isinstance(values, Iterable):
            err = Exception(
                "PromiseList requires an iterable. Received {}.".format(repr(values))
            )
            self.promise._reject_callback(err, False)
            return

        if not values:
            self._resolve([])
            return

        self._iterate(values)
        return

    def _iterate(self, values):
        # type: (Collection[Any]) -> None
        Promise = self._promise_class
        is_resolved = False

        self._length = len(values)
        self._values = [None] * self._length

        result = self.promise

        for i, val in enumerate(values):
            if Promise.is_thenable(val):
                maybe_promise = Promise._try_convert_to_promise(val)._target()
                # if is_resolved:
                #     # maybe_promise.suppressUnhandledRejections
                #     pass
                if maybe_promise.is_pending:
                    maybe_promise._add_callbacks(
                        partial(self._promise_fulfilled, i=i),
                        partial(self._promise_rejected, promise=maybe_promise),
                        None,
                    )
                    self._values[i] = maybe_promise
                elif maybe_promise.is_fulfilled:
                    is_resolved = self._promise_fulfilled(maybe_promise._value(), i)
                elif maybe_promise.is_rejected:
                    is_resolved = self._promise_rejected(
                        maybe_promise._reason(), promise=maybe_promise
                    )

            else:
                is_resolved = self._promise_fulfilled(val, i)

            if is_resolved:
                break

        if not is_resolved:
            result._is_async_guaranteed = True

    def _promise_fulfilled(self, value, i):
        # type: (Any, int) -> bool
        if self.is_resolved:
            return False
        self._values[i] = value  # type: ignore
        self._total_resolved += 1
        if self._total_resolved >= self._length:
            self._resolve(self._values)  # type: ignore
            return True
        return False

    def _promise_rejected(self, reason, promise):
        # type: (Exception, Promise) -> bool
        if self.is_resolved:
            return False
        self._total_resolved += 1
        self._reject(reason, traceback=promise._target()._traceback)
        return True

    @property
    def is_resolved(self):
        # type: () -> bool
        return self._values is None

    def _resolve(self, value):
        # type: (Collection[Any]) -> None
        assert not self.is_resolved
        assert not isinstance(value, self._promise_class)
        self._values = None
        self.promise._fulfill(value)

    def _reject(self, reason, traceback=None):
        # type: (Exception, Optional[TracebackType]) -> None
        assert not self.is_resolved
        self._values = None
        self.promise._reject_callback(reason, False, traceback=traceback)
