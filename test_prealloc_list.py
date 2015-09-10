import gc
import logging
import unittest
from prealloc_list import PreAllocatedList

log = logging.getLogger("test")


class PreAllocatedListTestCase(unittest.TestCase):

    def setUp(self):
        pass
        
    def tearDown(self):
        pass

    def testTruth(self):
        self.assertTrue(True)

    def testBasics(self):
        # Can create a PreAllocatedList
        lists = [PreAllocatedList()]
        alloc_lens = []
        length = 0
        while length < 100:
            lists.append(PreAllocatedList(length))
            alloc_lens.append(length)
            length = 3*length + 2

        # length at creation is zero
        for l in lists:
            self.assertEqual(len(l), 0)

        # Nothing there
        for l in lists:
            with self.assertRaises(IndexError):
                l[0]

        # Can append to
        for n, l in enumerate(lists):
            for i in range(n):
                v = (n + 2) * (i + 1) + 1
                l.append(v)

        # Contents accessable by index
        for n, l in enumerate(lists):
            for i in range(n):
                v = (n + 2) * (i + 1) + 1
                self.assertEqual(l[i], v)
            
        # Nothing beyond the end
        for n, l in enumerate(lists):
            self.assertEqual(len(l), n)
            with self.assertRaises(IndexError):
                l[len(l)]

        # Can pop
        for n, l in enumerate(lists):
            for i in range(len(l)-1, -1, -1):
                v = (n + 2) * (i + 1) + 1
                self.assertEqual(l.pop(), v)
        with self.assertRaises(IndexError):
            l.pop()


    def testBeyondPrealloc(self):
        # Can append beyond pre-allocated length
        a = PreAllocatedList(3)
        for i in range(5):
            a.append(str(i))
            for k in range(i+1):
                self.assertEqual(a[k], str(k))
            with self.assertRaises(IndexError):
                a[i+1]


def main():
    unittest.main()

if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    main()
