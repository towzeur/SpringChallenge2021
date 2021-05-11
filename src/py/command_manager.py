from typing import List
import re

from py.action import CompleteAction, GrowAction, SeedAction, WaitAction

import py.player
import py.game
import py.invalid_input_exception
import py.game_summary_manager

from py.java.compat import Singleton


class CommandManager(metaclass=Singleton):
    gameSummaryManager: py.game_summary_manager.GameSummaryManager = (
        py.game_summary_manager.GameSummaryManager()
    )

    PLAYER_WAIT_PATTERN: re.Pattern = re.compile(r"^WAIT(?:\s+(?P<message>.*))?")
    PLAYER_SEED_PATTERN: re.Pattern = re.compile(
        r"^SEED (?P<sourceId>\d+) (?P<targetId>\d+)(?:\s+(?P<message>.*))?"
    )
    PLAYER_GROW_PATTERN: re.Pattern = re.compile(
        r"^GROW (?P<targetId>\d+)(?:\s+(?P<message>.*))?"
    )
    PLAYER_COMPLETE_PATTERN: re.Pattern = re.compile(
        r"^COMPLETE (?P<targetId>\d+)(?:\s+(?P<message>.*))?"
    )

    def parseCommands(
        self, player: py.player.Player, lines: List[str], game: py.game.Game
    ):
        command: str = lines[0]

        if player.isWaiting():
            return

        try:
            match: re.Match

            # -- WAIT --
            match = CommandManager.PLAYER_WAIT_PATTERN.match(command)
            if match:
                player.setAction(WaitAction())
                self._matchMessage(player, match)
                return

            # -- GROW --
            if py.game.Game.ENABLE_GROW:
                match = CommandManager.PLAYER_GROW_PATTERN.match(command)
                if match:
                    targetId: int = int(match.group("targetId"))
                    player.setAction(GrowAction(targetId))
                    self._matchMessage(player, match)
                    return

            # -- COMPLETE --
            match = CommandManager.PLAYER_COMPLETE_PATTERN.match(command)
            if match:
                targetId: int = int(match.group("targetId"))
                player.setAction(CompleteAction(targetId))
                self._matchMessage(player, match)
                return

            # -- SEED --
            if py.game.Game.ENABLE_SEED:
                match = CommandManager.PLAYER_SEED_PATTERN.matcher(command)
                if match:
                    sourceId: int = int(match.group("sourceId"))
                    targetId: int = int(match.group("targetId"))
                    player.setAction(SeedAction(sourceId, targetId))
                    self._matchMessage(player, match)
                    return

            raise py.invalid_input_exception.InvalidInputException(
                py.game.Game.getExpected(), command
            )

        except py.invalid_input_exception.InvalidInputException as e:
            self.deactivatePlayer(player, str(e))
            CommandManager.gameSummaryManager.addPlayerBadCommand(player, e)
            CommandManager.gameSummaryManager.addPlayerDisqualified(player)

        except Exception as e:
            invalidInputException: py.invalid_input_exception.InvalidInputException = (
                py.invalid_input_exception.InvalidInputException(
                    py.game.Game.getExpected(), str(e)
                )
            )
            self.deactivatePlayer(player, str(invalidInputException))
            CommandManager.gameSummaryManager.addPlayerBadCommand(
                player, invalidInputException
            )
            CommandManager.gameSummaryManager.addPlayerDisqualified(player)

    def deactivatePlayer(self, player: py.player.Player, message: str):
        player.deactivate(self._escapeHTMLEntities(message))
        player.setScore(-1)

    def _escapeHTMLEntities(self, message: str) -> str:
        return message.replace("&lt", "<").replace("&gt", ">")

    def _matchMessage(self, player: py.player.Player, match: re.Match):
        message: str = match.group("message")
        if message:
            trimmed: str = message.strip()
            if len(trimmed) > 48:
                trimmed = trimmed[:46] + "..."
            player.setMessage(trimmed)
