from .Action import Action


class GrowAction(Action):
    def __init__(self, targetId: int):
        self.targetId = targetId

    def isGrow(self) -> bool:
        return True
