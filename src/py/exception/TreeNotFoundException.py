from .GameException import GameException


class TreeNotFoundException(GameException):
    def __init__(self, id: int):
        super().__init__(f"There is no tree on cell {id}")
