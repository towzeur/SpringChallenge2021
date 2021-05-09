from .GameException import GameException


class CellNotEmptyException(GameException):
    def __init__(self, id: int):
        super().__init__(f"There is already a tree on cell {id}")
