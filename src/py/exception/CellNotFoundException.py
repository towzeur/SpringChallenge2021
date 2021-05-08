

class CellNotFoundException(GameException):

    def __init__(self, id: int):
        super().__init__(f"Cell {id} not found")
    


