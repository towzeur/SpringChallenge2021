from .GameException import GameException


class AlreadyActivatedTree(GameException):
    def __init__(self, id: int):
        super().__init__(
            f"Tree on cell {id} is dormant (has already been used this round)"
        )
