import py

print(dir(py))


s = py.Seed()
print("seed", s.getOwner())

coord = py.CubeCoord(1, 1, 1)
cell = py.Cell(0)
b = py.Board({coord: cell})
print("board", b.coords, b.map)
print(b.coords[0].getOpposite())

cm = py.CommandManager()

print(dir(py.exception))
# from py.exception.CellNotValidException import CellNotValidException
raise py.exception.CellNotValidException.CellNotValidException(37)

r = py.Referee()
r.init()

exit()


# ------

from py.java.compat import Collections, Random

r = Random(seed=1337)

L = [i for i in range(10)]
print(L)  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

Collections.shuffle(L, r)
print(L)  # [3, 4, 1, 8, 7, 6, 0, 2, 5, 9]

# --
from Tree import Tree

Tree()


from Referee import Referee

Referee()
