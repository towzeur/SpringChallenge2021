from .GameException import GameException


class TreeNotTallException(GameException):
    def __init__(self, id: int):
        super().__init__(f"The tree on cell {id} is not large enough")
