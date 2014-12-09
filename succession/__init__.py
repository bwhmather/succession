from threading import Lock
from concurrent.futures import Future, CancelledError, TimeoutError


_UNDEFINED = object()


class ClosedError(Exception):
    pass


class _Chain(object):
    """ A linked list of futures.

    Each future yields a result and the next link in the chain
    """
    def __init__(self):
        self._next = Future()

    def push(self, value):
        next_ = _Chain()
        self._next.set_result((value, next_))
        return next_

    def close(self):
        self._next.cancel()

    def wait(self, timeout=None):
        try:
            result = self._next.result(timeout)
        except CancelledError:
            raise ClosedError()
        return result

    def wait_result(self, timeout=None):
        return self.wait(timeout)[0]

    def wait_next(self, timeout=None):
        return self.wait(timeout)[1]


class _SuccessionIterator(object):
    def __init__(self, head, prelude=None, timeout=None):
        if prelude is None:
            prelude = []
        self._prelude = iter(prelude)
        self._next = head
        self._timeout = timeout

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self._prelude)
        except StopIteration:
            # prelude empty, yield from chain
            pass

        try:
            result, self._next = self._next.wait(self._timeout)
            return result
        except TimeoutError:
            if self._timeout == 0:
                raise StopIteration()
            raise
        except ClosedError:
            raise StopIteration()


class Succession(object):
    def __init__(self, initial=None, drop=False, compress=None):
        self._lock = Lock()
        self._drop_after_push = drop
        self._compress_function = compress

        self._prelude = []
        self._root = _Chain()
        self._cursor = self._root

    def _head(self):
        """Same as `head` but does not attempt to acquire the succession lock
        """
        try:
            yield from self._iter(timeout=0)
        except TimeoutError:
            raise StopIteration()

    def head(self):
        """Returns a non-blocking iterator over all items that have already
        been added to the succession.
        """
        with self._lock:
            return self._head()

    def _iter(self, timeout=None):
        """Returns an iterator over items in the succession without acquiring
        the succession lock.
        """
        return _SuccessionIterator(
            self._root, prelude=self._prelude, timeout=timeout
        )

    def iter(self, timeout=None):
        """Returns an iterator over items in the succession.  Should be used
        instead of :py:func:`iter` if a timeout is desired.

        :param timeout:
            The time calls to :py:func:`next` should wait for an item before
            raising a :py:exception:`TimeoutError` exception.  If not provided
            the iterator will block indefinitely.  If zero the iterator will
            yield all items currently in the succession then raise
            :py:exception:`StopIteration` regardless of whether or not the
            sequence has been closed.
        """
        with self._lock:
            return self._iter(timeout=timeout)

    def __iter__(self):
        return self.iter()

    def push(self, value, *, drop=_UNDEFINED, compress=_UNDEFINED):
        drop = self._drop_after_push if drop is _UNDEFINED else drop
        drop = self._compress_function if compress is _UNDEFINED else compress

        with self._lock:
            self._cursor = self._cursor.push(value)
            if self._drop_after_push:
                self._root = self._cursor
            elif self._compress_function is not None:
                self._prelude = self._compress_function(self._head())
                self._root = self._cursor

    def close(self):
        """Stop further writes and notify all waiting listeners
        """
        with self._lock:
            self._cursor.close()

    def compress(self, function):
        """Applies function to an iterable of items in the succession and
        replaces the items with the result.

        :param function:
            A function taking an iterable of items and returning an equivalent
            iterable of items to replace them with
        """
        with self._lock:
            self._prelude = list(function(self._head()))
            self._root = self._cursor

    def drop(self):
        """Remove all items from the succession

        This does not affect existing iterators over the succession.
        """
        with self._lock:
            dropped = self._head()
            self._prelude = []
            self._root = self._cursor
            return dropped

__all__ = ['ClosedError', 'TimeoutError', 'Succession']
