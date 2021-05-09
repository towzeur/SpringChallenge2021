from .Action import Action


class WaitAction(Action):
    def isWait(self) -> bool:
        return True
