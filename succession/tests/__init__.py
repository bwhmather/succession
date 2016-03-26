import weakref
import gc
import threading
import unittest

from succession import _Chain, _SuccessionIterator, Succession, TimeoutError


class TestSuccession(unittest.TestCase):
    def test_chain(self):
        chain = _Chain()
        chain.push(2)
        self.assertEqual(chain.wait_result(), 2)
        self.assertIsInstance(chain.wait_next(), _Chain)

    def test_chain_iter(self):
        head = _Chain()
        chain = head

        for i in [1, 2, 3, 4, 5]:
            chain = chain.push(i)
        chain.close()

        self.assertEqual(list(_SuccessionIterator(head)), [1, 2, 3, 4, 5])

    def test_memory(self):
        # Make sure that chains don't hold references to previous links
        chain = _Chain()
        head = weakref.ref(chain)
        for i in range(1000):
            chain = chain.push(i)
        gc.collect()
        self.assertIsNone(head())

    def test_iter_memory(self):
        # Make sure that chain iterators do not hold a reference to the head
        chain = _Chain()

        def push_1000(chain):
            for i in range(1000):
                chain = chain.push(i)
        t = threading.Thread(target=push_1000, args=(chain,), daemon=True)

        iterator = _SuccessionIterator(chain)
        chain = weakref.ref(chain)

        t.start()
        for i in range(1000):
            next(iterator)

        t.join()

        gc.collect()
        self.assertIsNone(chain())

    def test_succession(self):
        succession = Succession()

        for i in [1, 2, 3, 4, 5]:
            succession.push(i)
        succession.close()

        self.assertEqual(list(succession), [1, 2, 3, 4, 5])

    def test_zero_timeout(self):
        succession = Succession()

        for i in [1, 2, 3, 4, 5]:
            succession.push(i)

        self.assertEqual(list(succession.iter(timeout=0)), [1, 2, 3, 4, 5])

    def test_nonzero_timeout(self):
        succession = Succession()

        for i in [1, 2, 3, 4, 5]:
            succession.push(i)

        result = []
        try:
            for item in succession.iter(timeout=0.01):
                result.append(item)
        except TimeoutError:
            self.assertEqual(result, [1, 2, 3, 4, 5])
        else:  # pragma:  no cover
            self.fail()

    def test_release_iter(self):
        succession = Succession(compress=lambda hd: [])
        root = weakref.ref(succession._root)
        iterator = weakref.ref(iter(succession))

        for i in [1, 2, 3, 4, 5]:
            succession.push(i)

        gc.collect()
        self.assertIsNone(root())
        self.assertIsNone(iterator())

    def test_compress_after_push(self):
        succession = Succession(compress=lambda items: [sum(items)])

        from_start = succession.iter()

        for i in [1, 2, 3, 4, 5]:
            succession.push(i)
        succession.close()

        from_end = succession.iter()

        self.assertEqual(list(from_start), [1, 2, 3, 4, 5])
        self.assertEqual(list(from_end), [15])

    def test_drop_after_push(self):
        succession = Succession(compress=lambda hd: [])

        from_start = succession.iter()

        for i in [1, 2, 3]:
            succession.push(i)

        from_middle = succession.iter()

        for i in [4, 5, 6]:
            succession.push(i)

        succession.close()

        from_end = succession.iter()

        self.assertEqual(list(from_start), [1, 2, 3, 4, 5, 6])
        self.assertEqual(list(from_middle), [4, 5, 6])
        self.assertEqual(list(from_end), [])

    def test_head(self):
        succession = Succession()

        self.assertEqual(list(succession.head()), [])

        for i in [1, 2, 3, 4, 5]:
            succession.push(i)

        self.assertEqual(list(succession.head()), [1, 2, 3, 4, 5])

        succession.close()

    def test_echo(self):
        req = Succession()
        res = Succession()

        def echo():
            for m in req:
                res.push(m)
            res.close()

        t = threading.Thread(target=echo)
        t.start()

        res_iter = iter(res)

        req.push(1)
        self.assertEqual(next(res_iter), 1)
        req.push(2)
        self.assertEqual(next(res_iter), 2)
        req.push(3)
        self.assertEqual(next(res_iter), 3)
        req.close()

        t.join()


loader = unittest.TestLoader()
suite = unittest.TestSuite((
    loader.loadTestsFromTestCase(TestSuccession),
))
