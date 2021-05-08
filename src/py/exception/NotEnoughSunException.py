
class NotEnoughSunException(GameException):

    def __init__(self, cost: int, sun: int):
        super().__init__("Not enough sun. You need {cost} but have {sun}")
    


