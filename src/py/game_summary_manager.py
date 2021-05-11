from typing import List

from py.codingame import GameManager
from py.java.compat import Singleton

import py.config
import py.cell
import py.player
import py.invalid_input_exception
import py.seed


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
        self,
        player: py.player.Player,
        invalidInputException: py.invalid_input_exception.InvalidInputException,
    ):
        self._add(
            GameManager.formatErrorMessage(
                f"{player.getNicknameToken()} provided invalid input. Expected '{invalidInputException.getExpected()}'\nGot '{invalidInputException.getGot()}'",
            )
        )

    def addPlayerTimeout(self, player: py.player.Player):
        self._add(
            GameManager.formatErrorMessage(
                f"{player.getNicknameToken()} has not provided an action in time.",
            )
        )

    def addPlayerDisqualified(self, player: py.player.Player):
        self._add(f"{player.getNicknameToken()} was disqualified.")

    def addCutTree(self, player: py.player.Player, cell: py.cell.Cell, score: int):
        self._add(
            f"{player.getNicknameToken()} is ending their tree life on cell {cell.getIndex()}, scoring {score} points"
        )

    def addGrowTree(self, player: py.player.Player, cell: py.cell.Cell):
        self._add(
            f"{player.getNicknameToken()} is growing a tree on cell {cell.getIndex()}"
        )

    def addPlantSeed(
        self,
        player: py.player.Player,
        targetCell: py.cell.Cell,
        sourceCell: py.cell.Cell,
    ):
        self._add(
            f"{player.getNicknameToken()} is planting a seed on cell {targetCell.getIndex()} from cell {sourceCell.getIndex()}"
        )

    def addWait(self, player: py.player.Player):
        self._add(f"{player.getNicknameToken()} is waiting")

    def addRound(self, round: int):
        self._add(f"Round {round}/{py.config.Config.MAX_ROUNDS - 1}")

    def addError(self, error: str):
        self._add(error)

    def addSeedConflict(self, seed: py.seed.Seed):
        self._add(f"py.seed.Seed conflict on cell {seed.getTargetCell()}")

    def addRoundTransition(self, round: int):
        self._add(f"Round {round} ends")
        if round + 1 < py.config.Config.MAX_ROUNDS:
            self._add(f"The sun is now pointing towards direction {(round + 1) % 6}")
            self._add(f"Round {round + 1} starts")

    def addGather(self, player: py.player.Player, given: int):
        self._add(f"{player.getNicknameToken()} has collected {given} sun points")
