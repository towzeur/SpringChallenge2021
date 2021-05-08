import abc

class Action(abc.ABC):

    NO_ACTION = None #Action()
    #public static final Action NO_ACTION = new Action() {
    #}

    def __init__(self):
        self.sourceId : int
        self.targetId : int


    def isGrow(self) -> bool:
        return False
    

    def isComplete(self) -> bool:
        return False
    

    def isSeed(self) -> bool:
        return False
    

    def isWait(self) -> bool:
        return False
    

    def getSourceId(self) -> int:
        return self.sourceId
    

    def getTargetId(self) -> int:
        return self.targetId

