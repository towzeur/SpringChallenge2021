from Action import Action


class CompleteAction(Action):

    def __init__(self, targetId: int):
        self.targetId = targetId
    

    def isComplete(self) -> bool:
        return True
    

