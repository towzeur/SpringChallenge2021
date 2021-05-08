

class TreeTooFarException(GameException):

    def __init__(self, from: int, to: int):
        super().__init__(f"The tree on cell {from} is too far from cell {to} to plant a seed there")

    

