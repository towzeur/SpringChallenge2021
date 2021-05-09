from typing import List

from Config import Config
from Cell import Cell
from Player import Player
from InvalidInputException import InvalidInputException
from Seed import Seed

from codingame import GameManager
from java_compat import Singleton


class GameSummaryManager(metaclass=Singleton):
    def __init__(self):
        self._lines: List[str] = list()

    def __str__(self):
        return "\n".join(self._lines)

    def getSummary(self) -> str:
        return self.__str__()

    def clear(self):
        self._lines.clear()

    def _add(self, message: str):
        self._lines.append(message)

    def addPlayerBadCommand(
        self, player: Player, invalidInputException: InvalidInputException
    ):
        self._add(
            GameManager.formatErrorMessage(
                f"{player.getNicknameToken()} provided invalid input. Expected '{invalidInputException.getExpected()}'\nGot '{invalidInputException.getGot()}'",
            )
        )

    def addPlayerTimeout(self, player: Player):
        self._add(
            GameManager.formatErrorMessage(
                f"{player.getNicknameToken()} has not provided an action in time.",
            )
        )

    def addPlayerDisqualified(self, player: Player):
        self._add(f"{player.getNicknameToken()} was disqualified.")

    def addCutTree(self, player: Player, cell: Cell, score: int):
        self._add(
            f"{player.getNicknameToken()} is ending their tree life on cell {cell.getIndex()}, scoring {score} points"
        )

    def addGrowTree(self, player: Player, cell: Cell):
        self._add(
            f"{player.getNicknameToken()} is growing a tree on cell {cell.getIndex()}"
        )

    def addPlantSeed(self, player: Player, targetCell: Cell, sourceCell: Cell):
        self._add(
            f"{player.getNicknameToken()} is planting a seed on cell {targetCell.getIndex()} from cell {sourceCell.getIndex()}"
        )

    def addWait(self, player: Player):
        self._add(f"{player.getNicknameToken()} is waiting")

    def addRound(self, round: int):
        self._add(f"Round {round}/{Config.MAX_ROUNDS - 1}")

    def addError(self, error: str):
        self._add(error)

    def addSeedConflict(self, seed: Seed):
        self._add(f"Seed conflict on cell {seed.getTargetCell()}")

    def addRoundTransition(self, round: int):
        self._add(f"Round {round} ends")
        if round + 1 < Config.MAX_ROUNDS:
            self._add(f"The sun is now pointing towards direction {(round + 1) % 6}")
            self._add(f"Round {round + 1} starts")

    def addGather(self, player: Player, given: int):
        self._add(f"{player.getNicknameToken()} has collected {given} sun points")
