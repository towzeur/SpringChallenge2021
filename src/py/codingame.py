import abc
from typing import List, Any
from enum import Enum
import re

from py.java.compat import Properties, Provider, Scanner

# ------------------------------------------------------------------------------
# GameManager.java
# ------------------------------------------------------------------------------


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
# Module.java
# ------------------------------------------------------------------------------


class Module(abc.ABC):  # interface
    @abc.abstractmethod
    def onGameInit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def onAfterGameTurn(self):
        raise NotImplementedError

    @abc.abstractmethod
    def onAfterOnEnd(self):
        raise NotImplementedError


# ------------------------------------------------------------------------------
# ViewModule.java
# ------------------------------------------------------------------------------


class ViewModule(Module):

    # def __init__(self, gameManager: GameManager, gameDataProvider: GameDataProvider):
    def __init__(self, gameManager: GameManager, gameDataProvider):
        self.gameManager = gameManager
        self.gameDataProvider = gameDataProvider

        # self.__gameManager: GameManager = None
        # self.__gameDataProvider: GameDataProvider = None

        # self.gameManager.registerModule(self)

    # @Override
    def onGameInit(self):
        # self.__sendGlobalData()
        # self.__sendFrameData()
        pass

    def __sendFrameData(self):
        # data: FrameViewData = gameDataProvider.getCurrentFrameData()
        # self.gameManager.setViewData("graphics", Serializer.serialize(data))
        pass

    def __sendGlobalData(self):
        # data: GlobalViewData = gameDataProvider.getGlobalData()
        # self.gameManager.setViewGlobalData("graphics", Serializer.serialize(data))
        pass

    # @Override
    def onAfterGameTurn(self):
        # self.sendFrameData()
        pass

    # @Override
    def onAfterOnEnd(self):
        ...


# ------------------------------------------------------------------------------
# EndScreenModule.java
# ------------------------------------------------------------------------------


class EndScreenModule(Module):

    # @Inject
    def __init__(self, gameManager: GameManager):
        # private
        self.gameManager: GameManager = None
        self.scores: List[int] = None
        self.displayedText: List[str] = None
        self.titleRankingsSprite: str = "logo.png"

        self.gameManager = gameManager
        gameManager.registerModule(self)

    def setScores(self, scores: List[int]):
        self.scores = scores

    def setScores(self, scores: List[int], displayedText: List[str]):
        self.scores = scores
        self.displayedText = displayedText

    def setTitleRankingsSprite(self, spriteName: str):
        self.titleRankingsSprite = spriteName

    def getTitleRankingsSprite(self) -> str:
        return self.titleRankingsSprite

    # @Override
    def onGameInit(self):
        ...

    # @Override
    def onAfterGameTurn(self):
        ...

    # @Override
    def onAfterOnEnd(self):
        data = (self.scores, self.titleRankingsSprite, self.displayedText)
        self.gameManager.setViewData("endScreen", data)


# ------------------------------------------------------------------------------
# Tooltip.java
# ------------------------------------------------------------------------------


class Tooltip:
    """
    The data for a tooltip which appears on the progress bar of the replay of a
    game to give information about significant game events. You may create
    several tooltips for the same turn.
    """

    def __init__(self, player: int, message: str):
        """
        Creates a tooltip which will appear on the replay of the current game.
        The tooltip will have the same color as one of the players.
        <p>
        The message to display is typically no longer than 30 characters.
        </p>

        @param player
                the index of the player the tooltip information is about.
        @param message
                the message to display in the tooltip.
        """
        self.player: int = player
        self.message: str = message


# ------------------------------------------------------------------------------
# OutputCommand.java
# ------------------------------------------------------------------------------


class OutputCommand(Enum):
    VIEW = 1
    INFOS = 2
    NEXT_PLAYER_INPUT = 3
    NEXT_PLAYER_INFO = 4
    SCORES = 5
    UINPUT = 6
    TOOLTIP = 7
    SUMMARY = 8
    METADATA = 9
    FAIL = 10

    def format(self, lineCount: int) -> str:
        # self.name, self.value
        return f"[[{self.name()}] {lineCount}]"


# ------------------------------------------------------------------------------
# InputCommand.java
# ------------------------------------------------------------------------------


class InputCommand:
    class Command(Enum):
        INIT = 1
        GET_GAME_INFO = 2
        SET_PLAYER_OUTPUT = 3
        SET_PLAYER_TIMEOUT = 4

    HEADER_PATTERN: re.Pattern = re.compile(
        r"\[\[(?P<cmd>.+)\] ?(?P<lineCount>[0-9]+)\]"
    )

    def __init__(self, cmd: "InputCommand.Command", lineCount: int):
        self.cmd: "InputCommand.Command" = cmd
        self.lineCount: int = lineCount

    @staticmethod
    def parse(line: str) -> "InputCommand":

        m: re.Match = InputCommand.HEADER_PATTERN.match(line)
        if not m.matches():
            raise RuntimeError("Error in data sent to referee")

        cmd: "InputCommand.Command" = InputCommand.Command.valueOf(m.group("cmd"))
        lineCount: int = int(m.group("lineCount"))
        return InputCommand(cmd, lineCount)


# ------------------------------------------------------------------------------
# AbstractPlayer.java
# ------------------------------------------------------------------------------


class AbstractPlayer(abc.ABC):
    class TimeoutException(Exception):
        serialVersionUID = 42

    def __init__(self):

        # @Inject
        # Provider<GameManager<AbstractPlayer>>
        self.gameManagerProvider: Provider = Provider(GameManager())

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
        self.gameManagerProvider.get().execute(self)
        self.hasBeenExecuted = True
        self.hasNeverBeenExecuted = False

    def getOutputs(self) -> List[str]:
        self.gameManagerProvider.get().setOuputsRead(True)
        if not self._hasBeenExecuted:
            raise RuntimeError("Can't get outputs without executing it!")

        if self.timeout:
            raise AbstractPlayer.TimeoutException()

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

    def deactivate(self, reason: str = None):
        self._active = False
        if reason:
            self.gameManagerProvider.get().addTooltip(Tooltip(self._index, reason))


# ------------------------------------------------------------------------------
# MultiplayerGameManager.java
# ------------------------------------------------------------------------------

# @Singleton
# <T extends AbstractMultiplayerPlayer> extends GameManager<T>
class MultiplayerGameManager(GameManager):
    def __init__(self):
        self._gameParameters: Properties = None
        self._seed: int = None

    # @Override protected
    def readGameProperties(self, iCmd: InputCommand, s: Scanner):
        # create game properties
        self._gameParameters = Properties()
        if iCmd.lineCount > 0:
            for i in range(iCmd.lineCount - 1):
                try:
                    self._gameParameters.load(StringReader(s.nextLine()))
                except IOException as e:
                    e.printStackTrace()

        self._seed = ThreadLocalRandom.current().nextLong()
        if "seed" in self._gameParameters:
            try:
                self._seed = Long.parseLong(self._gameParameters.getProperty("seed"))
            except NumberFormatException as e:
                log.warn(
                    "The seed property is not a number, it is reserved by the CodinGame platform to run arena games."
                )

        self._gameParameters.setProperty("seed", str(self._seed))

    # @Override protected
    def dumpGameProperties(self):
        msg: str = OutputCommand.UINPUT.format(self._gameParameters.size())
        out.println(msg)
        log.info(msg)

        for k, v in self._gameParameters.items():
            msg = f"{k}={v}"
            out.println(msg)
            log.info(msg)

    def getPlayerCount(self) -> int:
        return len(self.players)

    def getSeed(self) -> int:
        return self._seed

    def getGameParameters(self) -> Properties:
        return self._gameParameters

    def getPlayers(self) -> List[Any]:
        return self.players

    def getActivePlayers(self) -> List[Any]:
        # TODO: could be optimized with a list of active players updated on player.deactivate().
        return [p for p in self.players if p.isActive()]

    def getPlayer(self, i: int) -> Any:
        # throws IndexOutOfBoundsException:
        return self.players[i]

    def endGame(self):
        super().endGame()

    # @Override protected
    def allPlayersInactive(self) -> bool:
        return len(self.getActivePlayers()) == 0

    # @Override protected
    def getGameSummaryOutputCommand(self) -> OutputCommand:
        return OutputCommand.SUMMARY


# ------------------------------------------------------------------------------
# AbstractPlayer.java
# ------------------------------------------------------------------------------


class AbstractReferee(abc.ABC):
    """
    The Referee is the brain of your game, it implements all the rules and the turn order.
    """

    #
    # <p>
    # Called on startup, this method exists to create the initial state of the game, according to the given input.
    # </p>
    #
    @abc.abstractmethod
    def init(self):
        ...

    ##
    # Called on the computation of each turn of the game.
    # <p>
    # A typical game turn:
    # </p>
    # <ul>
    # <li>Send game information to each <code>Player</code> active on this turn.</li>
    # <li>Those players' code are <code>executed</code>.</li>
    # <li>Those players' inputs are read.</li>
    # <li>The game logic is applied.</li>
    # </ul>
    #
    # @param turn
    #            which turn of the game is currently being computed. Starts at 1.
    #
    @abc.abstractmethod
    def gameTurn(self, turn: int):
        ...

    ##
    # <p>
    # <i>Optional.</i>
    # </p>
    # This method is called once the final turn of the game is computed.
    # <p>
    # Typically, this method is used to set the players' final scores according to the final state of the game.
    # </p>
    #
    def onEnd(self):
        ...
