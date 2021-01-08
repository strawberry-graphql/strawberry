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

from pytest import raises

from strawberry.promise import Promise
from strawberry.promise.promise_list import PromiseList


def all(promises):
    return PromiseList(promises, Promise).promise


def test_empty_promises():
    all_promises = all([])
    assert all_promises.get() == []


def test_bad_promises():
    all_promises = all(None)

    with raises(Exception) as exc_info:
        all_promises.get()

    assert str(exc_info.value) == "PromiseList requires an iterable. Received None."


def test_promise_basic():
    all_promises = all([1, 2])
    assert all_promises.get() == [1, 2]


def test_promise_mixed():
    all_promises = all([1, 2, Promise.resolve(3)])
    assert all_promises.get() == [1, 2, 3]


def test_promise_rejected():
    e = Exception("Error")
    all_promises = all([1, 2, Promise.reject(e)])

    with raises(Exception) as exc_info:
        all_promises.get()

    assert str(exc_info.value) == "Error"


def test_promise_reject_skip_all_other_values():
    e1 = Exception("Error1")
    e2 = Exception("Error2")
    all_promises = all([1, Promise.reject(e1), Promise.reject(e2)])

    with raises(Exception) as exc_info:
        all_promises.get()

    assert str(exc_info.value) == "Error1"


def test_promise_lazy_promise():
    p = Promise()
    all_promises = all([1, 2, p])
    assert not all_promises.is_fulfilled
    p.do_resolve(3)
    assert all_promises.get() == [1, 2, 3]


def test_promise_contained_promise():
    p = Promise()
    all_promises = all([1, 2, Promise.resolve(None).then(lambda v: p)])
    assert not all_promises.is_fulfilled
    p.do_resolve(3)
    assert all_promises.get() == [1, 2, 3]
