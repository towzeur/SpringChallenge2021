import time
from typing import List, Any


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Random:
    """
    Java SE 6 random number generator
    Java's RNG is based on a classic Knuth-style linear congruential formula
    """

    def __init__(self, seed=None):
        self._seed = int(time.time() * 1000) if seed is None else seed
        self.nextNextGaussian = None

    def setSeed(self, seed):
        self._seed = seed

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, seed):
        self._seed = (seed ^ 0x5DEECE66D) & ((1 << 48) - 1)

    def next(self, bits):
        """
        Generate the next random number.
        As in Java, the general rule is that this method returns an int that
        is `bits` bits long, where each bit is nearly equally likely to be 0
        or 1.
        """
        bits = max(1, min(32, bits))  # clip to 1 - 32
        self._seed = (self._seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        retval = self._seed >> (48 - bits)
        # Python and Java don't really agree on how ints work. This converts
        # the unsigned generated int into a signed int if necessary.
        if retval & (1 << 31):
            retval -= 1 << 32
        return retval

    def nextBytes(self, l):
        raise NotImplementedError

    def nextInt(self, n=None):
        """
        Return a random int in [0, `n`).
        If `n` is not supplied, a random 32-bit integer will be returned.
        """
        if n is None:
            return self.next(32)

        if n <= 0:
            raise ValueError("Argument must be positive!")

        if not (n & (n - 1)):  # power of two?
            return (n * self.next(31)) >> 31

        bits = self.next(31)
        val = bits % n
        while (bits - val + n - 1) < 0:
            bits = self.next(31)
            val = bits % n

        return val

    def nextLong(self):
        raise NotImplementedError

    def nextBoolean(self):
        raise NotImplementedError

    def nextFloat(self):
        raise NotImplementedError

    def nextDouble(self):
        raise NotImplementedError

    def nextGaussian(self):
        raise NotImplementedError


class Properties:
    def __init__(self, filename=".properties"):
        self.filename = filename
        self._properties = Properties.load_properties(filename)

    @classmethod
    def load_properties(filename, sep="=", comment_char="#"):
        properties = {}
        with open(filename, "rt") as f:
            for line in f:
                l = line.strip()
                if l and not l.startswith(comment_char):
                    key_value = l.split(sep)
                    key = key_value[0].strip()
                    value = sep.join(key_value[1:]).strip().strip('"')
                    properties[key] = value
        return properties

    def getProperty(self, name: str) -> str:
        return self._properties.get(name, None)


class Collections:
    """
    https://hg.openjdk.java.net/jdk8/jdk8/jdk/file/687fd7c7986d/src/share/classes/java/util/Collections.java
    """

    @staticmethod
    def shuffle(lst: List[Any], rnd: Random):
        size: int = len(lst)
        for i in range(size, 1, -1):
            j: int = rnd.nextInt(i)
            lst[i - 1], lst[j] = lst[j], lst[i - 1]  # swap(arr, i-1, j);