import abc

from typing import List


class GameManager:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def formatErrorMessage(message: str) -> str:
        return f"{GameManager.FAIL}{message}{GameManager.ENDC}"


# ------------------------------------------------------------------------------
# AbstractPlayer.java
# ------------------------------------------------------------------------------


class AbstractPlayer(abc.ABC):
    # @Inject  

    gameManagerProvider : Provider<GameManager<AbstractPlayer>>

    class TimeoutException(Exception):
        serialVersionUID = 42

    def __init__(self):
        self._index: int = None
        self._inputs: List[str] = list()
        self._outputs: List[str] = list()
        self._timeout: bool = None
        self._score: int = None
        self._hasBeenExecuted: bool = None
        self._hasNeverBeenExecuted: bool = True

    def getNicknameToken(self) -> str:
        return f"${self._index}"

    def getAvatarToken(self) -> str:
        return f"${self._index}"

    def getIndex(self) -> int:
        return self._index

    def getScore(self) -> int:
        return self._score

    def setScore(self, score: int):
        self._score = score

    def sendInputLine(self, line: str):
        if self._hasBeenExecuted:
            raise RuntimeError("Impossible to send new inputs after calling execute")

        if self.gameManagerProvider.get().getOuputsRead():
            raise RuntimeError(
                "Sending input data to a player after reading any output is forbidden."
            )

        self.inputs.append(line)

    def execute(self):
        gameManagerProvider.get().execute(self)
        self.hasBeenExecuted = True
        self.hasNeverBeenExecuted = False

    def getOutputs(self) -> List[str]:
        self.gameManagerProvider.get().setOuputsRead(True)
        if not self._hasBeenExecuted:
            raise RuntimeError("Can't get outputs without executing it!")

        if self.timeout:
            raise TimeoutException()

        return self.outputs

    @abc.abstractmethod
    def getExpectedOutputLines(self) -> int:
        ...

    #
    # The following methods are only used by the GameManager:
    #

    def setIndex(self, index: int):
        self._index = index

    def getInputs(self) -> List[str]:
        return self._inputs

    def resetInputs(self):
        self._inputs = list()

    def resetOutputs(self):
        self._outputs = None

    def setOutputs(self, outputs: List[str]):
        self._outputs = outputs

    def setTimeout(self, timeout: bool):
        self.timeout = timeout

    def hasTimedOut(self) -> bool:
        return self._timeout

    def hasBeenExecuted(self) -> bool:
        return self._hasBeenExecuted

    def setHasBeenExecuted(self, hasBeenExecuted: bool):
        self._hasBeenExecuted = hasBeenExecuted

    def hasNeverBeenExecuted(self) -> bool:
        return self._hasNeverBeenExecuted


# ------------------------------------------------------------------------------
# AbstractMultiplayerPlayer.java
# ------------------------------------------------------------------------------


class AbstractMultiplayerPlayer(AbstractPlayer):
    def __init__(self):
        super().__init__()
        self._active: bool = True

    def getColorToken(self) -> int:
        return -(self.index + 1)

    def isActive(self) -> bool:
        return self._active

    def getIndex(self) -> int:
        return super().getIndex()

    def getScore(self) -> int:
        return super().getScore()

    def setScore(self, score: int):
        super().setScore(score)

    def deactivate(reason: str = None):
        self._active = False
        if reason:
            gameManagerProvider.get().addTooltip(Tooltip(index, reason))
