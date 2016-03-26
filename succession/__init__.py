from threading import Lock
from concurrent.futures import Future, CancelledError, TimeoutError


class ClosedError(Exception):
    pass


class _Chain(object):
    """ A linked list of futures.

    Each future yields a result and the next link in the chain
    """
    def __init__(self):
        self._next = Future()

    def push(self, value):
        """Sets the value of this link in the chain waking up all waiting
        listeners and returns a reference to the next link.
        """
        next_ = _Chain()
        self._next.set_result((value, next_))
        return next_

    def close(self):
        """Finish the chain at this link.  It will not given a value.

        All current and future listeners will be woken with a
        :exception:`ClosedError` and it will no longer be possible to add new
        links.
        """
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
    def __init__(self, *, compress=None):
        self._lock = Lock()
        self._compress_function = compress

        self._prelude = []
        # `_root` is a pointer to the current head of the chain.  It should
        # start where prelude finishes.
        self._root = _Chain()
        # `_cursor` is a pointer to first un-pushed link in the chain.
        self._cursor = self._root

    def _head(self):
        """Same as `head` but does not attempt to acquire the succession lock
        """
        return self._iter(timeout=0)

    def head(self):
        """Returns a non-blocking iterator over all items that have already
        been added to the succession.

        Synonym for ``iter(timeout=0)``
        """
        return self._head()

    def _iter(self, timeout=None):
        """Returns an iterator over items in the succession without acquiring
        the succession lock.
        """
        return _SuccessionIterator(
            self._root, prelude=self._prelude, timeout=timeout
        )

    def iter(self, timeout=None):
        """Returns an iterator over current and future items in the succession.

        Should be used instead of :func:`iter` if a timeout is desired.

        :param timeout:
            The time calls to :func:`next` should wait for an item before
            raising a :exception:`TimeoutError` exception.  If not provided
            the iterator will block indefinitely.  If zero the iterator will
            yield all items currently in the succession then raise
            :exception:`StopIteration` regardless of whether or not the
            sequence has been closed.
        """
        with self._lock:
            return self._iter(timeout=timeout)

    def __iter__(self):
        return self.iter()

    def push(self, value, *, compress=True):
        with self._lock:
            self._cursor = self._cursor.push(value)
            if compress and self._compress_function:
                self._prelude = list(self._compress_function(self._head()))
                self._root = self._cursor

    def close(self):
        """Stop further writes and notify all waiting listeners
        """
        with self._lock:
            self._cursor.close()


__all__ = ['ClosedError', 'TimeoutError', 'Succession']
