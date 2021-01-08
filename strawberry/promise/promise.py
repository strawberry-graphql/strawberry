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

from asyncio import Future, ensure_future
from functools import partial, wraps
from inspect import iscoroutine
from sys import exc_info
from threading import Event, Lock
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Hashable,
    Iterator,
    List,
    MutableMapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from weakref import WeakKeyDictionary

from six import reraise

from .async_ import Async
from .promise_list import PromiseList


class ImmediateScheduler(object):
    def call(self, fn):
        # type: (Callable) -> None
        try:
            fn()
        except Exception:
            pass

    def wait(self, promise, timeout=None):
        # type: (Promise, Optional[float]) -> None
        e = Event()

        def on_resolve_or_reject(_):
            # type: (Any) -> None
            e.set()

        promise._then(on_resolve_or_reject, on_resolve_or_reject)
        waited = e.wait(timeout)
        if not waited:
            raise Exception("Timeout")


def iterate_promise(promise: "Promise") -> Iterator:
    if not promise.is_fulfilled:
        yield from promise.future  # type: ignore
    assert promise.is_fulfilled
    return promise.get()


default_scheduler = ImmediateScheduler()

async_instance = Async()

_state_lock = Lock()

DEFAULT_TIMEOUT = None  # type: Optional[float]

MAX_LENGTH = 0xFFFF | 0
CALLBACK_SIZE = 3

CALLBACK_FULFILL_OFFSET = 0
CALLBACK_REJECT_OFFSET = 1
CALLBACK_PROMISE_OFFSET = 2

BASE_TYPES = (str, int, bool, float, complex, tuple, list, dict, bytes)

# These are the potential states of a promise
STATE_PENDING = -1
STATE_REJECTED = 0
STATE_FULFILLED = 1


def make_self_resolution_error() -> TypeError:
    return TypeError("Promise is self")


def try_catch(
    handler: Callable, *args: Any, **kwargs: Any
) -> Union[Tuple[Any, None], Tuple[None, Tuple[Exception, Optional[TracebackType]]]]:
    try:
        return (handler(*args, **kwargs), None)
    except Exception as e:
        tb = exc_info()[2]
        return (None, (e, tb))


T = TypeVar("T")
S = TypeVar("S", contravariant=True)


class Promise(Generic[T]):
    """
    This is the Promise class that complies
    Promises/A+ specification.
    """

    _state = STATE_PENDING  # type: int
    _is_final = False
    _is_bound = False
    _is_following = False
    _is_async_guaranteed = False
    _length = 0
    _handlers = None  # type: Dict[int, Union[Callable, Promise, None]]
    _fulfillment_handler0 = None  # type: Any
    _rejection_handler0 = None  # type: Any
    _promise0 = None  # type: Optional[Promise]
    _future = None  # type: Future
    _traceback = None  # type: Optional[TracebackType]
    _is_waiting = False
    _scheduler = None

    def __init__(self, executor=None, scheduler=None):
        # type: (Optional[Callable[[Callable[[T], None], Callable[[Exception], None]], None]], Any) -> None
        """
        Initialize the Promise into a pending state.
        """
        self._scheduler = scheduler

        if executor is not None:
            self._resolve_from_executor(executor)

    @property
    def scheduler(self) -> ImmediateScheduler:
        return self._scheduler or default_scheduler

    @property
    def future(self) -> Future:
        if not self._future:
            self._future = Future()  # type: ignore
            self._then(  # type: ignore
                self._future.set_result, self._future.set_exception
            )
        return self._future

    def __iter__(self) -> Iterator:
        return iterate_promise(self._target())

    __await__ = __iter__

    def _resolve_callback(self, value):
        # type: (T) -> None
        if value is self:
            return self._reject_callback(make_self_resolution_error(), False)

        if not self.is_thenable(value):
            return self._fulfill(value)

        promise = self._try_convert_to_promise(value)._target()
        if promise == self:
            self._reject(make_self_resolution_error())
            return

        if promise._state == STATE_PENDING:
            len = self._length
            if len > 0:
                promise._migrate_callback0(self)
            for i in range(1, len):
                promise._migrate_callback_at(self, i)

            self._is_following = True
            self._length = 0
            self._set_followee(promise)
        elif promise._state == STATE_FULFILLED:
            self._fulfill(promise._value())
        elif promise._state == STATE_REJECTED:
            self._reject(promise._reason(), promise._target()._traceback)

    def _settled_value(self, _raise=False):
        # type: (bool) -> Any
        assert not self._is_following

        if self._state == STATE_FULFILLED:
            return self._rejection_handler0
        elif self._state == STATE_REJECTED:
            if _raise:
                raise_val = self._fulfillment_handler0
                reraise(type(raise_val), raise_val, self._traceback)
            return self._fulfillment_handler0

    def _fulfill(self, value: T) -> None:
        if value is self:
            err = make_self_resolution_error()
            return self._reject(err)
        with _state_lock:
            self._state = STATE_FULFILLED
            self._rejection_handler0 = value

        if self._length > 0:
            if self._is_async_guaranteed:
                self._settle_promises()
            else:
                async_instance.settle_promises(self)

    def _reject(self, reason, traceback=None):
        # type: (Exception, Optional[TracebackType]) -> None
        with _state_lock:
            self._state = STATE_REJECTED
            self._fulfillment_handler0 = reason
            self._traceback = traceback

        if self._is_final:
            assert self._length == 0
            async_instance.fatal_error(reason, self.scheduler)
            return

        if self._length > 0:
            async_instance.settle_promises(self)
        else:
            self._ensure_possible_rejection_handled()

        if self._is_async_guaranteed:
            self._settle_promises()
        else:
            async_instance.settle_promises(self)

    def _ensure_possible_rejection_handled(self) -> None:
        pass

    def _reject_callback(
        self,
        reason: Exception,
        synchronous: bool = False,
        traceback: Optional[TracebackType] = None,
    ) -> None:
        assert isinstance(
            reason, Exception
        ), "A promise was rejected with a non-error: {}".format(reason)
        self._reject(reason, traceback)

    def _clear_callback_data_index_at(self, index: int) -> None:
        assert not self._is_following
        assert index > 0
        base = index * CALLBACK_SIZE - CALLBACK_SIZE
        self._handlers[base + CALLBACK_PROMISE_OFFSET] = None
        self._handlers[base + CALLBACK_FULFILL_OFFSET] = None
        self._handlers[base + CALLBACK_REJECT_OFFSET] = None

    def _fulfill_promises(self, length: int, value: T) -> None:
        for i in range(1, length):
            handler = self._fulfillment_handler_at(i)
            promise = self._promise_at(i)
            self._clear_callback_data_index_at(i)
            self._settle_promise(promise, handler, value, None)

    def _reject_promises(self, length: int, reason: Exception) -> None:
        for i in range(1, length):
            handler = self._rejection_handler_at(i)
            promise = self._promise_at(i)
            self._clear_callback_data_index_at(i)
            self._settle_promise(promise, handler, reason, None)

    def _settle_promise(
        self,
        promise: Optional["Promise"],
        handler: Optional[Callable],
        value: Union[T, Exception],
        traceback: Optional[TracebackType],
    ) -> None:
        assert not self._is_following
        is_promise = isinstance(promise, self.__class__)
        async_guaranteed = self._is_async_guaranteed
        if callable(handler):
            if promise is None or not is_promise:
                handler(value)
            else:
                if async_guaranteed:
                    promise._is_async_guaranteed = True
                self._settle_promise_from_handler(handler, value, promise)
        elif promise is not None and is_promise:
            if async_guaranteed:
                promise._is_async_guaranteed = True
            if self._state == STATE_FULFILLED:
                promise._fulfill(value)
            else:
                promise._reject(cast(Exception, value), self._traceback)

    def _settle_promise0(
        self,
        handler: Optional[Callable],
        value: Any,
        traceback: Optional[TracebackType],
    ) -> None:
        promise = self._promise0
        self._promise0 = None
        self._settle_promise(promise, handler, value, traceback)  # type: ignore

    def _settle_promise_from_handler(self, handler, value, promise):
        # type: (Callable, Any, Promise) -> None
        value, error_with_tb = try_catch(handler, value)  # , promise

        if error_with_tb:
            error, tb = error_with_tb
            promise._reject_callback(error, False, tb)
        else:
            promise._resolve_callback(value)

    def _promise_at(self, index):
        # type: (int) -> Optional[Promise]
        assert index > 0
        assert not self._is_following
        return self._handlers.get(  # type: ignore
            index * CALLBACK_SIZE - CALLBACK_SIZE + CALLBACK_PROMISE_OFFSET
        )

    def _fulfillment_handler_at(self, index):
        # type: (int) -> Optional[Callable]
        assert not self._is_following
        assert index > 0
        return self._handlers.get(  # type: ignore
            index * CALLBACK_SIZE - CALLBACK_SIZE + CALLBACK_FULFILL_OFFSET
        )

    def _rejection_handler_at(self, index):
        # type: (int) -> Optional[Callable]
        assert not self._is_following
        assert index > 0
        return self._handlers.get(  # type: ignore
            index * CALLBACK_SIZE - CALLBACK_SIZE + CALLBACK_REJECT_OFFSET
        )

    def _migrate_callback0(self, follower):
        # type: (Promise) -> None
        self._add_callbacks(
            follower._fulfillment_handler0,
            follower._rejection_handler0,
            follower._promise0,
        )

    def _migrate_callback_at(self, follower, index):
        self._add_callbacks(
            follower._fulfillment_handler_at(index),
            follower._rejection_handler_at(index),
            follower._promise_at(index),
        )

    def _add_callbacks(
        self,
        fulfill,  # type: Optional[Callable]
        reject,  # type: Optional[Callable]
        promise,  # type: Optional[Promise]
    ):
        # type: (...) -> int
        assert not self._is_following

        if self._handlers is None:
            self._handlers = {}

        index = self._length
        if index > MAX_LENGTH - CALLBACK_SIZE:
            index = 0
            self._length = 0

        if index == 0:
            assert not self._promise0
            assert not self._fulfillment_handler0
            assert not self._rejection_handler0

            self._promise0 = promise
            if callable(fulfill):
                self._fulfillment_handler0 = fulfill
            if callable(reject):
                self._rejection_handler0 = reject

        else:
            base = index * CALLBACK_SIZE - CALLBACK_SIZE

            assert (base + CALLBACK_PROMISE_OFFSET) not in self._handlers
            assert (base + CALLBACK_FULFILL_OFFSET) not in self._handlers
            assert (base + CALLBACK_REJECT_OFFSET) not in self._handlers

            self._handlers[base + CALLBACK_PROMISE_OFFSET] = promise
            if callable(fulfill):
                self._handlers[base + CALLBACK_FULFILL_OFFSET] = fulfill
            if callable(reject):
                self._handlers[base + CALLBACK_REJECT_OFFSET] = reject

        self._length = index + 1
        return index

    def _target(self):
        # type: () -> Promise
        ret = self
        while ret._is_following:
            ret = ret._followee()
        return ret

    def _followee(self):
        # type: () -> Promise
        assert self._is_following
        assert isinstance(self._rejection_handler0, Promise)
        return self._rejection_handler0

    def _set_followee(self, promise):
        # type: (Promise) -> None
        assert self._is_following
        assert not isinstance(self._rejection_handler0, Promise)
        self._rejection_handler0 = promise

    def _settle_promises(self):
        # type: () -> None
        length = self._length
        if length > 0:
            if self._state == STATE_REJECTED:
                reason = self._fulfillment_handler0
                traceback = self._traceback
                self._settle_promise0(self._rejection_handler0, reason, traceback)
                self._reject_promises(length, reason)
            else:
                value = self._rejection_handler0
                self._settle_promise0(self._fulfillment_handler0, value, None)
                self._fulfill_promises(length, value)

            self._length = 0

    def _resolve_from_executor(self, executor):
        # type: (Callable[[Callable[[T], None], Callable[[Exception], None]], None]) -> None
        synchronous = True

        def resolve(value: T) -> None:
            self._resolve_callback(value)

        def reject(
            reason: Exception, traceback: Optional[TracebackType] = None
        ) -> None:
            self._reject_callback(reason, synchronous, traceback)

        error = None
        traceback = None
        try:
            executor(resolve, reject)
        except Exception as e:
            traceback = exc_info()[2]
            error = e

        synchronous = False

        if error is not None:
            self._reject_callback(error, True, traceback)

    @classmethod
    def wait(cls, promise, timeout=None):
        # type: (Promise, Optional[float]) -> None
        async_instance.wait(promise, timeout)

    def _wait(self, timeout=None):
        # type: (Optional[float]) -> None
        self.wait(self, timeout)

    def get(self, timeout=None):
        # type: (Optional[float]) -> T
        self._wait(timeout or DEFAULT_TIMEOUT)
        return self._target_settled_value(_raise=True)

    def _target_settled_value(self, _raise=False):
        # type: (bool) -> Any
        with _state_lock:
            return self._target()._settled_value(_raise)

    _value = _reason = _target_settled_value
    value = reason = property(_target_settled_value)

    def __repr__(self):
        # type: () -> str
        hex_id = hex(id(self))
        if self._is_following:
            return "<Promise at {} following {}>".format(hex_id, self._target())
        state = self._state
        if state == STATE_PENDING:
            return "<Promise at {} pending>".format(hex_id)
        elif state == STATE_FULFILLED:
            return "<Promise at {} fulfilled with {}>".format(
                hex_id, repr(self._rejection_handler0)
            )
        elif state == STATE_REJECTED:
            return "<Promise at {} rejected with {}>".format(
                hex_id, repr(self._fulfillment_handler0)
            )

        return "<Promise unknown>"

    @property
    def is_pending(self):
        # type: (Promise) -> bool
        """Indicate whether the Promise is still pending. Could be wrong the moment the function returns."""
        return self._target()._state == STATE_PENDING

    @property
    def is_fulfilled(self):
        # type: (Promise) -> bool
        """Indicate whether the Promise has been fulfilled. Could be wrong the moment the function returns."""
        return self._target()._state == STATE_FULFILLED

    @property
    def is_rejected(self):
        # type: (Promise) -> bool
        """Indicate whether the Promise has been rejected. Could be wrong the moment the function returns."""
        return self._target()._state == STATE_REJECTED

    def catch(self, on_rejection):
        # type: (Promise, Callable[[Exception], Any]) -> Promise
        """
        This method returns a Promise and deals with rejected cases only.
        It behaves the same as calling Promise.then(None, on_rejection).
        """
        return self.then(None, on_rejection)

    def _then(
        self,
        did_fulfill=None,  # type: Optional[Callable[[T], S]]
        did_reject=None,  # type: Optional[Callable[[Exception], S]]
    ) -> "Promise[S]":
        promise = self.__class__()  # type: Promise
        with _state_lock:
            target = self._target()
            state = target._state
            if state == STATE_PENDING:
                target._add_callbacks(did_fulfill, did_reject, promise)

        if state != STATE_PENDING:
            traceback = None
            if state == STATE_FULFILLED:
                value = target._rejection_handler0
                handler = did_fulfill
            elif state == STATE_REJECTED:
                value = target._fulfillment_handler0
                traceback = target._traceback
                handler = did_reject  # type: ignore
            async_instance.invoke(
                partial(target._settle_promise, promise, handler, value, traceback),
                promise.scheduler
                # target._settle_promise instead?
                # settler,
                # target,
            )

        return promise

    fulfill = _resolve_callback
    do_resolve = _resolve_callback
    do_reject = _reject_callback

    def then(self, did_fulfill=None, did_reject=None):
        # type: (Promise, Callable[[T], S], Optional[Callable[[Exception], S]]) -> Promise[S]
        """
        This method takes two optional arguments.  The first argument
        is used if the "self promise" is fulfilled and the other is
        used if the "self promise" is rejected.  In either case, this
        method returns another promise that effectively represents
        the result of either the first of the second argument (in the
        case that the "self promise" is fulfilled or rejected,
        respectively).
        Each argument can be either:
          * None - Meaning no action is taken
          * A function - which will be called with either the value
            of the "self promise" or the reason for rejection of
            the "self promise".  The function may return:
            * A value - which will be used to fulfill the promise
              returned by this method.
            * A promise - which, when fulfilled or rejected, will
              cascade its value or reason to the promise returned
              by this method.
          * A value - which will be assigned as either the value
            or the reason for the promise returned by this method
            when the "self promise" is either fulfilled or rejected,
            respectively.
        :type success: (Any) -> object
        :type failure: (Any) -> object
        :rtype : Promise
        """
        return self._then(did_fulfill, did_reject)

    def done(self, did_fulfill=None, did_reject=None):
        # type: (Optional[Callable], Optional[Callable]) -> None
        promise = self._then(did_fulfill, did_reject)
        promise._is_final = True

    def done_all(self, handlers=None):
        # type: (Promise, Optional[List[Union[Dict[str, Optional[Callable]], Tuple[Callable, Callable], Callable]]]) -> None
        """
        :type handlers: list[(Any) -> object] | list[((Any) -> object, (Any) -> object)]
        """
        if not handlers:
            return

        for handler in handlers:
            if isinstance(handler, tuple):
                s, f = handler
                self.done(s, f)
            elif isinstance(handler, dict):
                s = handler.get("success")  # type: ignore
                f = handler.get("failure")  # type: ignore

                self.done(s, f)
            else:
                self.done(handler)

    def then_all(self, handlers=None):
        # type: (Promise, List[Callable]) -> List[Promise]
        """
        Utility function which calls 'then' for each handler provided. Handler can either
        be a function in which case it is used as success handler, or a tuple containing
        the success and the failure handler, where each of them could be None.
        :type handlers: list[(Any) -> object] | list[((Any) -> object, (Any) -> object)]
        :param handlers
        :rtype : list[Promise]
        """
        if not handlers:
            return []

        promises = []  # type: List[Promise]

        for handler in handlers:
            if isinstance(handler, tuple):
                s, f = handler

                promises.append(self.then(s, f))
            elif isinstance(handler, dict):
                s = handler.get("success")
                f = handler.get("failure")

                promises.append(self.then(s, f))
            else:
                promises.append(self.then(handler))

        return promises

    @classmethod
    def _try_convert_to_promise(cls, obj):
        # type: (Any) -> Promise
        _type = obj.__class__
        if issubclass(_type, Promise):
            if cls is not Promise:
                return cls(obj.then, obj._scheduler)
            return obj

        if iscoroutine(obj):  # type: ignore
            obj = ensure_future(obj)  # type: ignore
            _type = obj.__class__

        if is_future_like(_type):

            def executor(resolve, reject):
                # type: (Callable, Callable) -> None
                if obj.done():
                    _process_future_result(resolve, reject)(obj)
                else:
                    obj.add_done_callback(_process_future_result(resolve, reject))

            promise = cls(executor)  # type: Promise
            promise._future = obj
            return promise

        return obj

    @classmethod
    def reject(cls, reason):
        # type: (Exception) -> Promise
        ret = cls()  # type: Promise
        ret._reject_callback(reason, True)
        return ret

    rejected = reject

    @classmethod
    def resolve(cls, obj):
        # type: (T) -> Promise[T]
        if not cls.is_thenable(obj):
            ret = cls()  # type: Promise
            ret._state = STATE_FULFILLED
            ret._rejection_handler0 = obj
            return ret

        return cls._try_convert_to_promise(obj)

    cast = resolve
    fulfilled = cast

    @classmethod
    def promisify(cls, f):
        # type: (Callable) -> Callable[..., Promise]

        @wraps(f)
        def wrapper(*args, **kwargs):
            # type: (*Any, **Any) -> Promise
            def executor(resolve, reject):
                # type: (Callable, Callable) -> Optional[Any]
                return resolve(f(*args, **kwargs))

            return cls(executor)

        return wrapper

    _safe_resolved_promise = None  # type: Promise

    @classmethod
    def safe(cls, fn):
        # type: (Callable) -> Callable
        from functools import wraps

        if not cls._safe_resolved_promise:
            cls._safe_resolved_promise = Promise.resolve(None)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            # type: (*Any, **Any) -> Promise
            return cls._safe_resolved_promise.then(lambda v: fn(*args, **kwargs))

        return wrapper

    @classmethod
    def all(cls, promises):
        # type: (Any) -> Promise
        return PromiseList(promises, promise_class=cls).promise

    @classmethod
    def for_dict(cls, m):
        # type: (Dict[Hashable, Promise[S]]) -> Promise[Dict[Hashable, S]]
        """
        A special function that takes a dictionary of promises
        and turns them into a promise for a dictionary of values.
        In other words, this turns an dictionary of promises for values
        into a promise for a dictionary of values.
        """
        dict_type = type(m)  # type: Type[Dict]

        if not m:
            return cls.resolve(dict_type())  # type: ignore

        def handle_success(resolved_values):
            # type: (List[S]) -> Dict[Hashable, S]
            return dict_type(zip(m.keys(), resolved_values))

        return cls.all(m.values()).then(handle_success)

    @classmethod
    def is_thenable(cls, obj):
        # type: (Any) -> bool
        """
        A utility function to determine if the specified
        object is a promise using "duck typing".
        """
        _type = obj.__class__
        if obj is None or _type in BASE_TYPES:
            return False

        return (
            issubclass(_type, Promise)
            or iscoroutine(obj)  # type: ignore
            or is_future_like(_type)
        )


_type_done_callbacks = WeakKeyDictionary()  # type: MutableMapping[type, bool]


def is_future_like(_type):
    # type: (type) -> bool
    if _type not in _type_done_callbacks:
        _type_done_callbacks[_type] = callable(
            getattr(_type, "add_done_callback", None)
        )
    return _type_done_callbacks[_type]


promisify = Promise.promisify
promise_for_dict = Promise.for_dict
is_thenable = Promise.is_thenable


def _process_future_result(resolve, reject):
    # type: (Callable, Callable) -> Callable
    def handle_future_result(future):
        # type: (Any) -> None
        try:
            resolve(future.result())
        except Exception as e:
            tb = exc_info()[2]
            reject(e, tb)

    return handle_future_result
