import abc
from typing import List, Any, Dict
from enum import Enum
import re
import logging

from py.java.compat import Properties, Provider, Scanner, Singleton

# ------------------------------------------------------------------------------
# GameManager.java
# ------------------------------------------------------------------------------


class GameManager(abc.ABC): #<Any extends AbstractPlayer>: # abstract public 
    """
    The <code>GameManager</code> takes care of running each self.__turn of the game and 
    computing each visual frame of the replay. It provides many utility methods 
    that handle instances of your implementation of AbstractPlayer.

    @param [Any]
            Your implementation of AbstractPlayer
    """

    # ADDED
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    _log: Log = logging.getLogger('GameManager')

    __VIEW_DATA_TOTAL_SOFT_QUOTA: int = 512 # 1024
    __VIEW_DATA_TOTAL_HARD_QUOTA: int = 1024 # 1024
    __GAME_SUMMARY_TOTAL_HARD_QUOTA: int = 512 # 1024
    __GAME_SUMMARY_PER_TURN_HARD_QUOTA: int = 800
    __GAME_DURATION_HARD_QUOTA: int = 30_000
    __GAME_DURATION_SOFT_QUOTA: int = 25_000
    __MAX_TURN_TIME: int = __GAME_DURATION_SOFT_QUOTA
    __MIN_TURN_TIME: int = 50

    def __init__(self):
        #@Inject private
        self.__playerProvider: Provider[Any] = None
        self.__refereeProvider: Provider<AbstractReferee> = None
        self.__gson: Gson = None

        self._players: List[Any] = None
        self.__maxTurns: int = 200
        self.__turnMaxTime: int = 50
        self.__firstTurnMaxTime: int = 1000
        self.__turn: int = None
        frame: int = 0
        self.__gameEnd: bool = False
        self.__s: Scanner = None
        self._out: PrintStream = None
        self.__referee: AbstractReferee = None
        self.__newTurn: bool = None

        self.__currentTooltips: List[Tooltip] = list()
        self.__prevTooltips: List[Tooltip] = None 

        self.__currentGameSummary: List[str] = list()
        self.__prevGameSummary: List[str] = None
 
        self.__currentViewData: JsonObject = None
        self.__prevViewData: JsonObject = None

        self.__frameDuration: int = 1000

        self.__globalViewData: JsonObject = JsonObject()

        self.__registeredModules: List[Module] = list()

        self.__metadata: Dict[str, str] = dict()

        self.__initDone: bool = False
        self.__outputsRead: bool = False
        self.__totalViewDataBytesSent: int = 0
        self.__totalGameSummaryBytes: int = 0
        self.__totalTurnTime: int = 0

        self.__viewWarning: bool = None 
        self.__summaryWarning: bool = None

    #
    # GameManager main loop.
    # 
    # @param is
    #            input stream used to read commands from Game
    # @param out
    #            print stream used to issue commands to Game
    #
    def start(self, is: InputStream, out: PrintStream):
        self.__s = Scanner(is)
        try:
            self._out = out
            self.self.__referee = self.__refereeProvider.get()

            # Init ---------------------------------------------------------------
            self._log.info("Init")
            iCmd: InputCommand = InputCommand.parse(self.__s.nextLine())
            playerCount: int = self.__s.nextInt()
            self.__s.nextLine()
            self._players = list()

            for i in range(playerCount):
                player: Any = self.__playerProvider.get()
                player.setIndex(i)
                self._players.add(player)
            

            self._readGameProperties(iCmd, self.__s)

            self.__prevViewData = None
            self.__currentViewData = JsonObject()

            self.__referee.init()
            for module in self.__registeredModules:
                module.onGameInit()
            self.__initDone = True

            # Game Loop ----------------------------------------------------------
            self.__turn = 1
            while self.__turn <= self.getMaxTurns() and not self.isGameEnd() and not self._allPlayersInactive():
                self.__swapInfoAndViewData()
                self._log.info("Turn " + self.__turn)
                self.__newTurn = True
                self.__outputsRead = False # Set as True after first getOutputs() to forbid sendInputs

                self.__referee.gameTurn(self.__turn)
                for module in self.__registeredModules:
                    module.onAfterGameTurn()

                # Create a frame if no player has been executed
                if (not self._players.isEmpty() and self._players.stream().noneMatch(p -> p.hasBeenExecuted())):
                    self._execute(self._players.get(0), 0)
                

                # reset self._players' outputs
                for player in self._players:
                    player.resetOutputs()
                    player.setHasBeenExecuted(False)

                self.__turn += 1 # end of the foor loop 
                
            

            self._log.info("End")

            self.__referee.onEnd()
            for module in self.__registeredModules:
                module.onAfterOnEnd()

            # Send last frame ----------------------------------------------------
            self.__swapInfoAndViewData()
            self.__newTurn = True

            self.__dumpView()
            self.__dumpInfos()

            self._dumpGameProperties()
            self.__dumpMetadata()
            self.__dumpScores()

            self.__s.close()

        except (Throwable e):
            self.__dumpFail(e)
            self.__s.close()
            raise e
        
    
    @abc.abstractmethod
    def _allPlayersInactive(self) -> bool:
        ...

    abc.abstractmethod
    def _readGameProperties(self, iCmd: InputCommand , s: Scanner):
        ...


    def _execute(self, player: Any, nbrOutputLines: int=None):
        if nbrOutputLines is None:
            nbrOutputLines = player.getExpectedOutputLines()

        try:
            if (not self.self.__initDone):
                raise RuntimeException("Impossible to execute a player during init phase.")
            

            player.setTimeout(False)

            InputCommand iCmd = InputCommand.parse(self.__s.nextLine())

            if (iCmd.cmd != InputCommand.Command.GET_GAME_INFO):
                raise RuntimeException("Invalid command: " + iCmd.cmd)
            

            self.__dumpView()
            self.__dumpInfos()
            self.__dumpNextPlayerInput(player.getInputs().toArray(str[0]))
            if (nbrOutputLines > 0):
                self.__addTurnTime()
            
            self.__dumpNextPlayerInfos(player.getIndex(), nbrOutputLines, player.hasNeverBeenExecuted() ? self.__firstTurnMaxTime : self.__turnMaxTime)

            # READ PLAYER OUTPUTS
            iCmd = InputCommand.parse(self.__s.nextLine())
            if (iCmd.cmd == InputCommand.Command.SET_PLAYER_OUTPUT):
                output: List[str] = list()
                for (int i = 0 i < iCmd.lineCount i++):
                    output.add(self.__s.nextLine())
                
                player.setOutputs(output)
            elif (iCmd.cmd == InputCommand.Command.SET_PLAYER_TIMEOUT):
                player.setTimeout(True)
             else:
                raise RuntimeException("Invalid command: " + iCmd.cmd)
            

            player.resetInputs()
            self.__newTurn = False
         except (Throwable e):
            #Don't let the user except game fail exceptions
            self.__dumpFail(e)
            raise e
        
    
    def __swapInfoAndViewData(self):
        self.__prevViewData = self.__currentViewData
        self.__currentViewData = JsonObject()

        self.__prevGameSummary = self.__currentGameSummary
        self.__currentGameSummary = list()

        self.__prevTooltips = self.__currentTooltips
        self.__currentTooltips = list()
    

    def _dumpGameProperties(self):
        ...
    

    def __dumpMetadata(self):
        OutputData data = OutputData(OutputCommand.METADATA)
        data.add(self.__getMetadata())
        self._out.println(data)
    

    def __dumpScores(self):
        OutputData data = OutputData(OutputCommand.SCORES)
        List[str] playerScores = list()
        for (AbstractPlayer player : self._players):
            playerScores.add(player.getIndex() + " " + player.getScore())
        
        data.addAll(playerScores)
        self._out.println(data)
    

    def __dumpFail(self, e: Throwable):
        OutputData data = OutputData(OutputCommand.FAIL)
        strWriter sw = strWriter()
        PrintWriter pw = PrintWriter(sw)
        e.printStackTrace(pw)

        data.add(sw.tostr())
        self._out.println(data)
    

    def __dumpView(self):
        data: OutputData = OutputData(OutputCommand.VIEW)
        if (self.__newTurn):
            data.add("KEY_FRAME " + frame)
            if (self.__turn == 1):
                JsonObject initFrame = JsonObject()
                initFrame.add("global", self.__globalViewData)
                initFrame.add("frame", self.__prevViewData)
                data.add(initFrame.tostr())
             else:
                data.add(self.__prevViewData.tostr())
            
         else:
            data.add("INTERMEDIATE_FRAME " + frame)
        
        viewData: str = data.tostr()

        self.__totalViewDataBytesSent += viewData.length()
        if (self.__totalViewDataBytesSent > self.__VIEW_DATA_TOTAL_HARD_QUOTA):
            raise RuntimeException("The amount of data sent to the viewer is too big!")
        elif (self.__totalViewDataBytesSent > self.__VIEW_DATA_TOTAL_SOFT_QUOTA and not self.__viewWarning):
            self._log.warn(
                "Warning: the amount of data sent to the viewer is too big.\nPlease try to optimize your code to send less data (try replacing some commitEntityStates by a commitWorldState)."
            )
            self.__viewWarning = True
        

        self._log.info(viewData)
        self._out.println(viewData)

        frame++
    

    def __dumpInfos(self):
        data: OutputData = OutputData(OutputCommand.INFOS)
        self._out.println(data)

        if (self.__newTurn and self.__prevGameSummary != None):
            OutputData summary = OutputData(self._getGameSummaryOutputCommand())
            summary.addAll(self.__prevGameSummary)
            self._out.println(summary)
        

        if (self.__newTurn and self.__prevTooltips != None and not self.__prevTooltips.isEmpty()):
            data = OutputData(OutputCommand.TOOLTIP)
            for (Tooltip t : self.__prevTooltips):
                data.add(t.message)
                data.add(str.valueOf(t.player))
            
            self._out.println(data)
        
    
    @abc.abstractmethod
    def _getGameSummaryOutputCommand(self) -> OutputCommand:

    def __dumpNextPlayerInfos(self, nextPlayer: int, expectedOutputLineCount: int, timeout: int):
        data: OutputData = OutputData(OutputCommand.NEXT_PLAYER_INFO)
        data.add(str.valueOf(nextPlayer))
        data.add(str.valueOf(expectedOutputLineCount))
        data.add(str.valueOf(timeout))
        self._out.println(data)
    

    def __dumpNextPlayerInput(self, input: str[]):
        data: OutputData = OutputData(OutputCommand.NEXT_PLAYER_INPUT)
        data.addAll(input)
        self._out.println(data)
        if (self._log.isInfoEnabled()):
            self._log.info(data)
        
    

    def __getMetadata(self) -> str:
        return self.__gson.toJsonTree(self.__metadata).getAsJsonObject().tostr()
    

    def setOuputsRead(self, self.__outputsRead: bool):
        self.self.__outputsRead = self.__outputsRead
    

    def getOuputsRead(self) -> bool:
        return self.self.__outputsRead
    

    #
    # Public methods used by Referee:
    #

    def putMetadata(self, key: str, value: str):
        self.__metadata.put(key, value)
    

    def setFrameDuration(self, self.__frameDuration: int):
        if (self.__frameDuration <= 0):
            raise IllegalArgumentException("Invalid frame duration: only positive frame duration is supported")
        elif (self.self.__frameDuration != self.__frameDuration):
            self.self.__frameDuration = self.__frameDuration
            self.__currentViewData.addProperty("duration", self.__frameDuration)
        
    


    def getFrameDuration(self) -> int:
        return self.__frameDuration
    

    def _endGame(self):
        self.self.__gameEnd = True
    


    def isGameEnd(self) -> bool:
        return self.self.__gameEnd
    


    def setMaxTurns(self, self.__maxTurns: int): # throws IllegalArgumentException:
        if (self.__maxTurns <= 0):
            raise IllegalArgumentException("Invalid maximum number of turns")
        
        self.self.__maxTurns = self.__maxTurns
    

    def getMaxTurns(self) -> int:
        return self.__maxTurns
    


    def setTurnMaxTime(self, self.__turnMaxTime: int): # throws IllegalArgumentException:
        if (self.__turnMaxTime < self.__MIN_TURN_TIME):
            raise IllegalArgumentException("Invalid self.__turn max time : stay above 50ms")
        elif (self.__turnMaxTime > self.__MAX_TURN_TIME):
            raise IllegalArgumentException("Invalid self.__turn max time : stay under 25s")
        
        self.self.__turnMaxTime = self.__turnMaxTime
    
    

    def setFirstTurnMaxTime(self, self.__firstTurnMaxTime: int): #throws IllegalArgumentException:
        if (self.__firstTurnMaxTime < self.__MIN_TURN_TIME):
            raise IllegalArgumentException("Invalid turn max time : stay above 50ms")
        elif (self.__firstTurnMaxTime > self.__MAX_TURN_TIME):
            raise IllegalArgumentException("Invalid turn max time : stay under 25s")
        
        self.self.__firstTurnMaxTime = self.__firstTurnMaxTime
    


    def getTurnMaxTime(self) -> int:
        return self.__turnMaxTime
    
    

    def getFirstTurnMaxTime(self) -> int:
        return self.__firstTurnMaxTime
    

    def setViewData(self, data: Object):
        setViewData("default", data)
    

    def setViewData(self, moduleName: str, data: Object):
        self.self.__currentViewData.add(moduleName, self.__gson.toJsonTree(data))
    

    def setViewGlobalData(self, moduleName: str, data: Object):
        if (self.__initDone):
            raise IllegalStateException("Impossible to send global data to view outside of init phase")
        
        self.self.__globalViewData.add(moduleName, self.__gson.toJsonTree(data))
    


    def addTooltip(self, tooltip: Tooltip):
        self.self.__currentTooltips.add(tooltip)
    


    def addTooltip(self, player: AbstractPlayer, message: str):
        addTooltip(Tooltip(player.getIndex(), message))
    


    def addToGameSummary(self, summary: str):
    
        total: int = sum([len(x) for x in self.self.__currentGameSummary])

        if (total < self.__GAME_SUMMARY_PER_TURN_HARD_QUOTA and total + self.__totalGameSummaryBytes < self.__GAME_SUMMARY_TOTAL_HARD_QUOTA):
            self.self.__currentGameSummary.add(summary)
            self.__totalGameSummaryBytes += total
        elif (not self.__summaryWarning):
            self._log.warn("Warning: the game summary is full. Please try to send less data.")
            self.__summaryWarning = True
        
    

    def __addTurnTime(self):
        self.__totalTurnTime += self.__turnMaxTime
        if (self.__totalTurnTime > self.__GAME_DURATION_HARD_QUOTA):
            raise RuntimeException(f"Total game duration too long (>{self.__GAME_DURATION_HARD_QUOTA}ms)")
        elif (self.__totalTurnTime > self.__GAME_DURATION_SOFT_QUOTA):
            self._log.warn(f"Warning: too many turns and/or too much time allocated to self._players per self.__turn ({self.__totalTurnTime}ms/{self.__GAME_DURATION_HARD_QUOTA}ms)")
        
    
    def registerModule(self, module: Module):
        self.__registeredModules.add(module)
    

    def getLeagueLevel(self) -> int:
        return int(System.getProperty("league.level", "1"))
    

    @staticmethod
    def formatSuccessMessage(message: str) -> str:
        return f"{GameManager.OKGREEN}{message}{GameManager.ENDC}"
    
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
class MultiplayerGameManager(GameManager, metaclass=Singleton):
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
