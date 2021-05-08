

class Sun:

    def __init__(self):
        self._orientation : int = None

    def getOrientation(self) -> int:
        return self._orientation
    
    def setOrientation(self, orientation: int):
        self._orientation = (orientation) % 6
    
    def move(self):
        self._orientation = (self._orientation + 1) % 6
    
