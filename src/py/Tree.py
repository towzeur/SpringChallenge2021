import py.player


class Tree:
    def __init__(self):
        self._size: int = None
        self._owner: py.player.Player = None
        self._fatherIndex: int = -1
        self._isDormant: bool = None

    def getFatherIndex(self) -> int:
        return self._fatherIndex

    def setFatherIndex(self, fatherIndex: int):
        self._fatherIndex = fatherIndex

    def getOwner(self) -> py.player.Player:
        return self._owner

    def setOwner(self, owner: py.player.Player):
        self._owner = owner

    def getSize(self) -> int:
        return self._size

    def setSize(self, size: int):
        self._size = size

    def grow(self):
        self._size += 1

    def isDormant(self) -> bool:
        return self._isDormant

    def setDormant(self):
        self._isDormant = True

    def reset(self):
        self._isDormant = False
