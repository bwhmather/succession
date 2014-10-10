import weakref
import gc
import threading
import unittest

from succession import _Chain, _SuccessionIterator, Succession


class TestSuccession(unittest.TestCase):
    def test_chain(self):
        chain = _Chain()
        chain.push(2)
        self.assertEqual(chain.wait_result(), 2)

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

    def test_compress(self):
        def accumulate(start, new):
            return [sum(start) + new]

        succession = Succession(compress=accumulate)

        from_start = succession.iter()

        for i in [1, 2, 3, 4, 5]:
            succession.push(i)
        succession.close()

        from_end = succession.iter()

        self.assertEqual(list(from_start), [1, 2, 3, 4, 5])
        self.assertEqual(list(from_end), [15])

loader = unittest.TestLoader()
suite = unittest.TestSuite((
    loader.loadTestsFromTestCase(TestSuccession),
))
