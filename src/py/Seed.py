

class Seed:

    def __init__(self):
        self._owner : int = None
        self._sourceCell : int = None
        self._targetCell : int = None

    def getOwner(self) -> int:
        return self._owner
    

    def setOwner(self, owner: int):
        self._owner = owner
    

    def getSourceCell(self) -> int:
        return self._sourceCell
    

    def setSourceCell(self, sourceCell: int):
        self.sourceCell = sourceCell
    

    def getTargetCell(self) -> int:
        return self._targetCell
    

    def setTargetCell(self, targetCell: int):
        self.targetCell = targetCell
    


