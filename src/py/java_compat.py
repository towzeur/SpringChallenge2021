import time

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
        bits = max(1, min(32, bits)) # clip to 1 - 32
        self._seed = (self._seed * 0x5DEECE66D + 0xb) & ((1 << 48) - 1)
        retval = self._seed >> (48 - bits)
        # Python and Java don't really agree on how ints work. This converts
        # the unsigned generated int into a signed int if necessary.
        if retval & (1 << 31):
            retval -= (1 << 32)
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

        if not (n & (n - 1)): # power of two?
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

