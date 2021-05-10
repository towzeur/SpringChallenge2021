import sys
from typing import List

from codingame.AbstractPlayer import TimeoutException
from codingame import AbstractReferee
from MultiplayerGameManager import MultiplayerGameManager

#import com.codingame.gameengine.module.endscreen.EndScreenModule


#import com.codingame.view.ViewModule
#import com.google.inject.Inject
#import com.google.inject.Singleton

from Config import Config
from FrameType import FrameType
from CommandManager import CommandManager
from Game import Game
from GameSummaryManager import GameSummaryManager


self._viewModule: ViewModule = None
self._endScreenModule: EndScreenModule = None

#@Singleton
class Referee(AbstractReferee):

    def __init__(self):

        #@Inject private 
        self._gameManager: MultiplayerGameManager<Player> = None
        self._commandManager: CommandManager = None
        self._game: Game = None
        self._endScreenModule: EndScreenModule = None
        self._viewModule: ViewModule = None
        self._gameSummaryManager: GameSummaryManager = None

        # public
        self.seed: int = None
        self.maxFrames: int = None

    #@Override
    def init(self):
        self.seed = self._gameManager.getSeed()

        try:
            Config.load(self._gameManager.getGameParameters())
            Config.export(self._gameManager.getGameParameters())
            self._gameManager.setFirstTurnMaxTime(1000)
            self._gameManager.setTurnMaxTime(100)

            self._gameManager.setFrameDuration(500)

            self._game.init(self.seed)
            self._sendGlobalInfo()

        except Exception as e:
            e.printStackTrace()
            print("Referee failed to initialize", file=sys.stderr)
            self._abort()

    

    def _abort(self):
        print("Unexpected self._game end", file=sys.stderr)
        self._gameManager.endGame()
    

    def _sendGlobalInfo(self):
        for player in self._gameManager.getActivePlayers():
            for line in self._game.getGlobalInfoFor(player):
                player.sendInputLine(line)
            
    

    #@Override
    def gameTurn(self, turn: int):
        self._game.resetGameTurnData()

        if self._game.getCurrentFrameType() == FrameType.ACTIONS:
            # Give input to players
            for player in self._gameManager.getActivePlayers():
                if not player.isWaiting():
                    for line in self._game.getCurrentFrameInfoFor(player):
                        player.sendInputLine(line)
                    
                    player.execute()
                
            
            # Get output from players
            self._handlePlayerCommands()
        

        self._game.performGameUpdate()
    

    def _handlePlayerCommands(self):
        for player in self._gameManager.getActivePlayers():
            if not player.isWaiting():
                try:
                    self._commandManager.parseCommands(player, player.getOutputs(), self._game)
                except TimeoutException as e:
                    self._commandManager.deactivatePlayer(player, "Timeout!")
                    self._gameSummaryManager.addPlayerTimeout(player)
                    self._gameSummaryManager.addPlayerDisqualified(player)
                
            
    #@Override
    def onEnd(self):
        self._endScreenModule.setTitleRankingsSprite("logo.png")
        self._game.onEnd()

        scores: List[int] = [p.getScore() for p in self._gameManager.getPlayers()]
        displayedText: str = [p.getBonusScore() for p in self._gameManager.getPlayers()]
        self._endScreenModule.setScores(scores, displayedText)
    


