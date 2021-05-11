import abc
from typing import Dict, List, Any

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
    
    _log: Log = LogFactory.getLog(GameManager.class)

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
        OutputData data = OutputData(OutputCommand.VIEW)
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
        
        str viewData = data.tostr()

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
        return f"¤GREEN¤{message}§GREEN§"
    
    @staticmethod
    def formatErrorMessage(message: str) -> str:
        return f"¤RED¤{message}§RED§"
    
