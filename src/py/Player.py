# package com.codingame.game
from action.Action import Action
from Config import Config

from codingame import AbstractMultiplayerPlayer


class Player(AbstractMultiplayerPlayer):
    def __init__(self):
        self._message: str = None
        self._action: Action = Action.NO_ACTION
        self._sun: int = Config.STARTING_SUN
        self._waiting: bool = False
        self._bonusScore: int = 0

    # @Override
    def getExpectedOutputLines(self) -> int:
        return 1

    def addScore(self, score: int):
        self.setScore(self.getScore() + score)

    def reset(self):
        self._message = None
        self._action = Action.NO_ACTION

    def getMessage(self) -> str:
        return self._message

    def setMessage(self, message: str):
        self._message = message

    def setAction(self, action: Action):
        self._action = action

    def getAction(self) -> Action:
        return self._action

    def getSun(self) -> int:
        return self._sun

    def setSun(self, sun: int):
        self._sun = sun

    def addSun(self, sun: int):
        self._sun += sun

    def removeSun(self, amount: int):
        self._sun = max(0, self._sun - amount)

    def isWaiting(self) -> bool:
        return self._waiting

    def setWaiting(self, waiting: bool):
        self._waiting = waiting

    def getBonusScore(self) -> str:
        if self._bonusScore > 0:
            return f"{self.getScore() - self._bonusScore} points and {self._bonusScore} trees"
        else:
            return ""

    def addBonusScore(self, bonusScore: int):
        self._bonusScore += bonusScore
