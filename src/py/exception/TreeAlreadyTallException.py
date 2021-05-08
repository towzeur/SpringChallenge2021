
class TreeAlreadyTallException(GameException):

    def __init__(self, id: int):
        super().__init__(f"Tree on cell {id} cannot grow more (max size is 3).")
    


