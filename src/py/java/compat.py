import time
from typing import List, Any


class Provider:
    def __init__(self, provided):
        self.provided = provided

    def get(self):
        return self.provided


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


# ------------------------------------------------------------------------------


class Scanner:
    """
    Equivalent of java.util.Scanner
    """

    def __init__(self, data):

        if isinstance(data, str):
            self._stream = data.split()

        self._pos = 0
        self._len = len(self._stream)

    def close(self):
        raise NotImplementedError

    def delimiter(self) -> "pattern":
        """get the Pattern which the Scanner class is currently using to match delimiters."""
        raise NotImplementedError

    def findAll(self) -> "Stream<MatchResult>":
        """find a stream of match results that match the provided pattern str."""
        raise NotImplementedError

    def findInLine(self) -> str:
        """It is used to find the next occurrence of a pattern constructed from the specified str, ignoring delimiters."""
        raise NotImplementedError

    def findWithinHorizon(self) -> str:
        """It is used to find the next occurrence of a pattern constructed from the specified str, ignoring delimiters."""
        raise NotImplementedError

    def hasNext(self) -> bool:
        """It returns true if this scanner has another token in its input."""
        raise NotImplementedError

    def hasNextBigDecimal(self) -> bool:
        """It is used to check if the next token in this scanner's input can be interpreted as a BigDecimal using the nextBigDecimal() method or not."""
        raise NotImplementedError

    def hasNextBigInteger(self) -> bool:
        """It is used to check if the next token in this scanner's input can be interpreted as a BigDecimal using the nextBigDecimal() method or not."""
        raise NotImplementedError

    def hasNextBoolean(self) -> bool:
        """It is used to check if the next token in this scanner's input can be interpreted as a Boolean using the nextBoolean() method or not."""
        raise NotImplementedError

    def hasNextByte(self) -> bool:
        """It is used to check if the next token in this scanner's input can be interpreted as a Byte using the nextBigDecimal() method or not."""
        raise NotImplementedError

    def hasNextDouble(self) -> bool:
        """It is used to check if the next token in this scanner's input can be interpreted as a BigDecimal using the nextByte() method or not."""
        raise NotImplementedError

    def hasNextFloat(self) -> bool:
        """It is used to check if the next token in this scanner's input can be interpreted as a Float using the nextFloat() method or not."""
        raise NotImplementedError

    def hasNextInt(self) -> bool:
        """It is used to check if the next token in this scanner's input can be interpreted as an int using the nextInt() method or not."""
        raise NotImplementedError

    def hasNextLine(self) -> bool:
        """It is used to check if there is another line in the input of this scanner or not."""
        raise NotImplementedError

    def hasNextLong(self) -> bool:
        """It is used to check if the next token in this scanner's input can be interpreted as a Long using the nextLong() method or not."""
        raise NotImplementedError

    def hasNextShort(self) -> bool:
        """It is used to check if the next token in this scanner's input can be interpreted as a Short using the nextShort() method or not."""
        raise NotImplementedError

    def ioException(self) -> "IOException":
        """It is used to get the IOException last thrown by this Scanner's readable."""
        raise NotImplementedError

    def locale(self) -> "Locale":
        """It is used to get a Locale of the Scanner class."""
        raise NotImplementedError

    def match(self) -> "MatchResult":
        """It is used to get the match result of the last scanning operation performed by this scanner."""
        raise NotImplementedError

    def next(self) -> str:
        """It is used to get the next complete token from the scanner which is in use."""
        raise NotImplementedError

    def nextBigDecimal(self) -> "BigDecimal":
        """It scans the next token of the input as a BigDecimal."""
        raise NotImplementedError

    def nextBigInteger(self) -> "BigInteger":
        """It scans the next token of the input as a BigInteger."""
        raise NotImplementedError

    def nextBoolean(self) -> bool:
        """It scans the next token of the input into a bool value and returns that value."""
        raise NotImplementedError

    def nextByte(self) -> "byte":
        """It scans the next token of the input as a byte."""
        raise NotImplementedError

    def nextDouble(self) -> "double":
        """It scans the next token of the input as a double."""
        raise NotImplementedError

    def nextFloat(self) -> "float":
        """It scans the next token of the input as a float."""
        raise NotImplementedError

    def nextInt(self) -> int:
        """It scans the next token of the input as an Int."""
        raise NotImplementedError

    def nextLine(self) -> str:
        """It is used to get the input str that was skipped of the Scanner object."""
        raise NotImplementedError

    def nextLong(self) -> "long":
        """It scans the next token of the input as a long."""
        raise NotImplementedError

    def nextShort(self) -> "short":
        """It scans the next token of the input as a short."""
        raise NotImplementedError

    def radix(self) -> int:
        """It is used to get the default radix of the Scanner use."""
        raise NotImplementedError

    def remove(self):
        """It is used when remove operation is not supported by this implementation of Iterator."""
        raise NotImplementedError

    def reset(self) -> "Scanner":
        """It is used to reset the Scanner which is in use."""
        raise NotImplementedError

    def skip(self) -> "Scanner":
        """It skips input that matches the specified pattern, ignoring delimiters"""
        raise NotImplementedError

    def tokens(self) -> "Stream<str>":
        """It is used to get a stream of delimiter-separated tokens from the Scanner object which is in use."""
        raise NotImplementedError

    def toString(self) -> str:
        """It is used to get the str representation of Scanner using."""
        raise NotImplementedError

    def useDelimiter(self) -> "Scanner":
        """It is used to set the delimiting pattern of the Scanner which is in use to the specified pattern."""
        raise NotImplementedError

    def useLocale(self) -> "Scanner":
        """It is used to sets this scanner's locale object to the specified locale."""
        raise NotImplementedError

    def useRadix(self) -> "Scanner":
        """It is used to set the default radix of the Scanner which is in use to the specified radix."""
        raise NotImplementedError
