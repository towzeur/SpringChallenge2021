from .GameException import GameException


class CellNotValidException(GameException):
    def __init__(self, id: int):
        super().__init__(f"You can't plant a seed on cell {id}")
