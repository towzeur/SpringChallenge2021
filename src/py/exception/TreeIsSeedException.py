

class TreeIsSeedException(GameException):

    def __init__(self, id: int):
        super().__init__(f"The seed on {id} cannot produce seeds")
    


