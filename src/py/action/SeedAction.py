from .Action import Action


class SeedAction(Action):
    def __init__(self, sourceId: int, targetId: int):
        self.sourceId = sourceId
        self.targetId = targetId

    def isSeed(self) -> bool:
        return True
