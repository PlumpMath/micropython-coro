"""A list-like thing whose backing store is pre-allocated on creation"""
# This exists to prevent append() from forcing a heap allocation later on that
# may be unsatisfiable because of fragmentation. If the creation succeeds, you've
# got the capacity you asked for. That's the goal.
#
# The original motivation was to back the heapq in async_pyb

class PreAllocatedList:

    def __init__(self, palen=0):
        l = self.l = list(None for i in range(palen))
        self.length = 0

        '''
        def ni(*args):
            raise NotImplementedError

        self.clear = ni
        self.copy = ni
        self.count = ni
        self.extend = ni
        self.index = ni
        self.insert = ni
        self.remove = ni
        self.reverse = ni
        self.sort = ni
        '''

    def __len__(self):
        return self.length

    def __getitem__(self, k):
        if k >= self.length:
            raise IndexError('list index out of range')
        return self.l[k]

    def __setitem__(self, k, v):
        if k >= self.length:
            raise IndexError('list index out of range')
        self.l[k] = v

    def __iter__(self):
        l = self.l
        return (l[i] for i in range(self.length))

    def __contains__(self, v):
        return any(v == a for a in self)

    def append(self, v):
        a = self.length
        l = self.l
        if a < len(l):
            l[a] = v
        else:
            l.append(v)
        self.length = a + 1

    def pop(self):              # Warning: Doesn't implement pop(i)
        a = self.length - 1
        if a < 0:
            raise IndexError('pop from empty list')
        rv = self.l[a]
        self.length = a
        return rv

    def __repr__(self):
        return '[' + ', '.join(repr(v) for v in self) + ']'
