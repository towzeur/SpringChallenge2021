
class Cell:

    NO_CELL = Cell(-1, valid=False) # : 'Cell' =
        
    def __init__(self, index: int, valid: bool = True):
        self._valid = valid
        self._richness : int = None
        self._index : int = index
    

    def getIndex(self) -> int:
        return self._index if self._valid else -1
    

    def isValid(self) -> bool:
        return self._valid
    

    def setRichness(self, richness: int):
        self._richness = richness
    

    def getRichness(self) -> int:
        return self._richness
    


