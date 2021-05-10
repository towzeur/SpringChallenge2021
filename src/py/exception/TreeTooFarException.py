from .GameException import GameException


class TreeTooFarException(GameException):
    def __init__(self, from_cell: int, to_cell: int):
        super().__init__(
            f"The tree on cell {from_cell} is too far from cell {to_cell} to plant a seed there"
        )
