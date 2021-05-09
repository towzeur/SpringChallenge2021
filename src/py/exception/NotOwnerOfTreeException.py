# import com.codingame.game.Player
from .GameException import GameException


class NotOwnerOfTreeException(GameException):
    def __init__(self, id: int, player: Player):
        super().__init__(f"The tree on cell {id} is owned by opponent")
