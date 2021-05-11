import sys
from typing import List, Dict

from py.exception.AlreadyActivatedTree import AlreadyActivatedTree
from py.exception.CellNotEmptyException import CellNotEmptyException
from py.exception.CellNotFoundException import CellNotFoundException
from py.exception.CellNotValidException import CellNotValidException
from py.exception.GameException import GameException
from py.exception.NotEnoughSunException import NotEnoughSunException
from py.exception.NotOwnerOfTreeException import NotOwnerOfTreeException
from py.exception.TreeAlreadyTallException import TreeAlreadyTallException
from py.exception.TreeIsSeedException import TreeIsSeedException
from py.exception.TreeNotFoundException import TreeNotFoundException
from py.exception.TreeNotTallException import TreeNotTallException
from py.exception.TreeTooFarException import TreeTooFarException

from py.action.Action import Action

from py.codingame import MultiplayerGameManager

from py.java.compat import Singleton, Random, Collections

import py.board
import py.board_generator
import py.constants
import py.config
import py.cube_coord
import py.seed
import py.sun
import py.tree
import py.cell
import py.frame_type
import py.player
import py.game_summary_manager


class Game(metaclass=Singleton):
    # static
    ENABLE_SEED: bool = None
    ENABLE_GROW: bool = None
    ENABLE_SHADOW: bool = None
    ENABLE_HOLES: bool = None
    MAX_ROUNDS: int = None
    STARTING_TREE_COUNT: int = None
    STARTING_TREE_SIZE: int = None
    STARTING_TREE_DISTANCE: int = None
    STARTING_TREES_ON_EDGES: bool = None

    def __init__(self):
        # public
        self.nutrients: int = None
        self.board: py.board.Board = None
        self.trees: Dict[int, py.tree.Tree] = None
        self.dyingTrees: List[py.cube_coord.CubeCoord] = None
        self.availableSun: List[int] = None
        self.sentSeeds: List[py.seed.Seed] = None
        self.sun: py.sun.Sun = None
        self.shadows: Dict[int, int] = None
        self.cells: List[py.cell.Cell] = None
        self.random: Random = None
        self.round: int = None
        self.turn: int = None
        self.currentFrameType: py.frame_type.FrameType = None
        self.nextFrameType: py.frame_type.FrameType = None

        # private
        # self._gameManager: MultiplayerGameManager<py.player.Player> = None #@Inject private
        self._gameManager: MultiplayerGameManager = None  # @Inject private
        self._gameSummaryManager: py.game_summary_manager.GameSummaryManager = (
            None  # @Inject private
        )

    def init(self, seed: int):

        if self._gameManager.getLeagueLevel() == 1:
            # Wood 2
            Game.MAX_ROUNDS = 1
            Game.ENABLE_SEED = False
            Game.ENABLE_GROW = False
            Game.ENABLE_SHADOW = False
            Game.ENABLE_HOLES = False
            Game.STARTING_TREE_COUNT = 6
            Game.STARTING_TREE_SIZE = py.constants.Constants.TREE_TALL
            Game.STARTING_TREE_DISTANCE = 0
            Game.STARTING_TREES_ON_EDGES = False

        elif self._gameManager.getLeagueLevel() == 2:
            # Wood 1
            Game.MAX_ROUNDS = 6
            Game.ENABLE_SEED = False
            Game.ENABLE_GROW = True
            Game.ENABLE_SHADOW = False
            Game.ENABLE_HOLES = False
            Game.STARTING_TREE_COUNT = 4
            Game.STARTING_TREE_SIZE = py.constants.Constants.TREE_SMALL
            Game.STARTING_TREE_DISTANCE = 1
            Game.STARTING_TREES_ON_EDGES = False

        else:
            # Bronze+
            Game.MAX_ROUNDS = py.config.Config.Game.MAX_ROUNDS
            Game.ENABLE_SEED = True
            Game.ENABLE_GROW = True
            Game.ENABLE_SHADOW = True
            Game.ENABLE_HOLES = True
            Game.STARTING_TREE_COUNT = py.constants.Constants.Game.STARTING_TREE_COUNT
            Game.STARTING_TREE_SIZE = py.constants.Constants.TREE_SMALL
            Game.STARTING_TREE_DISTANCE = 2
            Game.STARTING_TREES_ON_EDGES = True

        self.nutrients = py.config.Config.STARTING_NUTRIENTS
        self.board = py.board_generator.BoardGenerator.generate(self.random)
        self.trees = dict()  # TreeMap<>()
        self.dyingTrees = list()
        # ArrayList<>(self._gameManager.getPlayerCount()) # CHECK
        self.availableSun = list()
        self.sentSeeds = list()
        self.sun = py.sun.Sun()
        self.shadows = dict()
        self.cells = list()
        self.random = Random(seed)
        self.round = 0
        self.turn = 0
        self.currentFrameType = py.frame_type.FrameType.INIT
        self.nextFrameType = py.frame_type.FrameType.GATHERING

        self.initStartingTrees()
        self.sun.setOrientation(0)
        if Game.ENABLE_SHADOW:
            self._calculateShadows()

    @staticmethod
    def getExpected() -> str:
        if not Game.ENABLE_GROW and not Game.ENABLE_SEED:
            return "COMPLETE <idx> | WAIT"

        if not Game.ENABLE_SEED and Game.ENABLE_GROW:
            return "GROW <idx> | COMPLETE <idx> | WAIT"

        return "SEED <from> <to> | GROW <idx> | COMPLETE <idx> | WAIT"

    def _getCoordByIndex(self, index: int) -> py.cube_coord.CubeCoord:
        for cubecoord, cell in self.board.map.items():
            if cell.getIndex() == index:
                return cubecoord
        raise CellNotFoundException(index)

    def initStartingTrees(self):

        startingCoords: List[py.cube_coord.CubeCoord] = list()
        if Game.STARTING_TREES_ON_EDGES:
            startingCoords = self._getBoardEdges()
        else:
            startingCoords = [
                coord for coord in self.board.coords if not coord.isOrigin()
            ]

        startingCoords = [
            coord
            for coord in self.board.coords
            if self.board.map[coord].getRichness()
            != py.constants.Constants.RICHNESS_NULL
        ]

        validCoords: List[py.cube_coord.CubeCoord] = list()
        while len(validCoords) < Game.STARTING_TREE_COUNT * 2:
            validCoords = self._tryInitStartingTrees(startingCoords)

        players: List[py.player.Player] = self._gameManager.getPlayers()
        for i in range(Game.STARTING_TREE_COUNT):
            self._placeTree(
                players[0],
                self.board.map[validCoords.get(2 * i)].getIndex(),
                Game.STARTING_TREE_SIZE,
            )
            self._placeTree(
                players[1],
                self.board.map[validCoords.get(2 * i + 1)].getIndex(),
                Game.STARTING_TREE_SIZE,
            )

    def _tryInitStartingTrees(
        self, startingCoords: List[py.cube_coord.CubeCoord]
    ) -> List[py.cube_coord.CubeCoord]:
        coordinates: List[py.cube_coord.CubeCoord] = list()
        for i in range(Game.STARTING_TREE_COUNT):
            if not startingCoords:
                return coordinates
            r: int = self.random.nextInt(len(startingCoords))
            normalCoord: py.cube_coord.CubeCoord = startingCoords[r]
            oppositeCoord: py.cube_coord.CubeCoord = normalCoord.getOpposite()
            startingCoords = [
                coord
                for coord in startingCoords
                if not (
                    coord.distanceTo(normalCoord) <= Game.STARTING_TREE_DISTANCE
                    or coord.distanceTo(oppositeCoord) <= Game.STARTING_TREE_DISTANCE
                )
            ]
            coordinates.append(normalCoord)
            coordinates.append(oppositeCoord)
        return coordinates

    def _calculateShadows(self):
        self.shadows.clear()
        for index, tree in self.trees.items():
            coord: py.cube_coord.CubeCoord = self.board.coords[index]
            for i in range(1, tree.getSize() + 1):
                tempCoord: py.cube_coord.CubeCoord = coord.neighbor(
                    self.sun.getOrientation(), i
                )
                if tempCoord in self.board.map:
                    key: int = self.board.map[tempCoord].getIndex()
                    value: int = max(
                        self.shadows.get(key, tree.getSize()), tree.getSize()
                    )  # CHECK
                    self.shadows[key] = value

    def _getBoardEdges(self) -> List[py.cube_coord.CubeCoord]:
        return [
            coord
            for coord in self.board.coords
            if coord.norm() == py.config.Config.MAP_RING_COUNT
        ]

    def getCurrentFrameInfoFor(self, player: py.player.Player) -> List[str]:
        lines: List[str] = list()
        lines.append(str(self.round))
        lines.append(str(self.nutrients))

        # py.player.Player information, receiving player first
        other: py.player.Player = self._gameManager.getPlayer(1 - player.getIndex())
        lines.append(f"{player.getSun()} {player.getScore()}")
        lines.append(
            f"{other.getSun()} {other.getScore()} {1 if other.isWaiting() else 0}"
        )
        lines.append(f"{len(self.trees)}")

        for index, tree in self.trees.items():
            lines.append(
                "{} {} {} {}".format(
                    index,
                    tree.getSize(),
                    1 if (tree.getOwner() == player) else 0,
                    1 if tree.isDormant() else 0,
                )
            )

        possibleMoves: List[str] = self._getPossibleMoves(player)
        lines.append(str(len(possibleMoves)))
        for possiblemove in possibleMoves:
            lines.append(possiblemove)

        return lines

    def _getCoordsInRange(
        self, center: py.cube_coord.CubeCoord, N: int
    ) -> List[py.cube_coord.CubeCoord]:
        results: List[py.cube_coord.CubeCoord] = list()
        for x in range(-N, N + 1):
            for y in range(max(-N, -x - N), min(+N, -x + N) + 1):
                z: int = -x - y
                results.append(
                    py.cube_coord.CubeCoord.cubeAdd(
                        center, py.cube_coord.CubeCoord(x, y, z)
                    )
                )
        return results

    def _getPossibleMoves(self, player: py.player.Player) -> List[str]:
        lines: List[str] = list()
        lines.append("WAIT")

        possibleSeeds: List[str] = list()
        possibleGrows: List[str] = list()
        possibleCompletes: List[str] = list()

        if player.isWaiting():
            return lines

        # For each tree, where they can seed.
        # For each tree, if they can grow.
        seedCost: int = self._getSeedCost(player)
        for index, tree in [
            (index, tree)
            for (index, tree) in self.trees.items()
            if tree.getOwner() == player
        ]:
            coord: py.cube_coord.CubeCoord = self.board.coords.get(index)

            if self._playerCanSeedFrom(player, tree, seedCost):
                for targetCoord in self._getCoordsInRange(coord, tree.getSize()):
                    targetCell: py.cell.Cell = self.board.map.get(
                        targetCoord, py.cell.Cell.NO_CELL
                    )
                    if self._playerCanSeedTo(targetCell, player):
                        possibleSeeds.append(f"SEED {index} {targetCell.getIndex()}")

            growCost: int = self._getGrowthCost(tree)
            if growCost <= player.getSun() and not tree.isDormant():
                if tree.getSize() == py.constants.Constants.TREE_TALL:
                    possibleCompletes.append(f"COMPLETE {index}")
                elif Game.ENABLE_GROW:
                    possibleGrows.append(f"GROW {index}")

        for possibleList in (possibleCompletes, possibleGrows, possibleSeeds):
            Collections.shuffle(possibleList, self.random)
            # CHECK
            lines.extend(possibleList)

        return lines

    def _playerCanSeedFrom(
        self, player: py.player.Player, tree: py.tree.Tree, seedCost: int
    ) -> bool:
        return (
            Game.ENABLE_SEED
            and (seedCost <= player.getSun())
            and (tree.getSize() > py.constants.Constants.TREE_SEED)
            and (not tree.isDormant())
        )

    def playerCanSeedTo(
        self, targetCell: py.cell.Cell, player: py.player.Player
    ) -> bool:
        return (
            targetCell.isValid()
            and (targetCell.getRichness() != py.constants.Constants.RICHNESS_NULL)
            and (targetCell.getIndex() not in self.trees)
        )

    def getGlobalInfoFor(self, player: py.player.Player) -> List[str]:
        lines: List[str] = list()
        lines.append(str(len(self.board.coords)))

        for coord in self.board.coords:
            cell: py.cell.Cell = self.board.map[coord]
            lines.append(
                f"{cell.getIndex()} {cell.getRichness()} {self._getNeighbourIds(coord)}"
            )

        return lines

    def getNeighbourIds(self, coord: py.cube_coord.CubeCoord) -> str:
        orderedNeighborIds: List[int] = [
            self.board.map.get(coord.neighbor(i), py.cell.Cell.NO_CELL).getIndex()
            for i in range(len(py.cube_coord.CubeCoord.directions))
        ]
        return " ".join(orderedNeighborIds)

    def resetGameTurnData(self):
        self.dyingTrees.clear()
        self.availableSun.clear()
        self.sentSeeds.clear()
        for player in self._gameManager.getPlayers():
            self.availableSun.append(player.getSun())
            player.reset()
        self.currentFrameType = self.nextFrameType

    def _getGrowthCost(self, targetTree: py.tree.Tree) -> int:
        targetSize: int = targetTree.getSize() + 1
        if targetSize > py.constants.Constants.TREE_TALL:
            return py.constants.Constants.LIFECYCLE_END_COST
        return self._getCostFor(targetSize, targetTree.getOwner())

    def _getSeedCost(self, player: py.player.Player) -> int:
        return self._getCostFor(0, player)

    def _doGrow(self, player: py.player.Player, action: Action):
        coord: py.cube_coord.CubeCoord = self._getCoordByIndex(action.getTargetId())
        cell: py.cell.Cell = self.board.map.get(coord)
        targetTree: py.tree.Tree = self.trees.get(cell.getIndex())

        if targetTree is None:
            raise TreeNotFoundException(cell.getIndex())

        if targetTree.getOwner() != player:
            raise NotOwnerOfTreeException(cell.getIndex(), targetTree.getOwner())

        if targetTree.isDormant():
            raise AlreadyActivatedTree(cell.getIndex())

        if targetTree.getSize() >= py.constants.Constants.TREE_TALL:
            raise TreeAlreadyTallException(cell.getIndex())

        costOfGrowth: int = self._getGrowthCost(targetTree)
        currentSun: int = self.availableSun[player.getIndex()]
        if currentSun < costOfGrowth:
            raise NotEnoughSunException(costOfGrowth, player.getSun())

        self.availableSun.set(player.getIndex(), currentSun - costOfGrowth)

        targetTree.grow()
        self._gameSummaryManager.addGrowTree(player, cell)

        targetTree.setDormant()

    def _doComplete(self, player: py.player.Player, action: Action):
        coord: py.cube_coord.CubeCoord = self._getCoordByIndex(action.getTargetId())
        cell: py.cell.Cell = self.board.map[coord]
        targetTree: py.tree.Tree = self.trees.get(cell.getIndex(), None)
        if targetTree is None:
            raise TreeNotFoundException(cell.getIndex())

        if targetTree.getOwner() != player:
            raise NotOwnerOfTreeException(cell.getIndex(), targetTree.getOwner())

        if targetTree.getSize() < py.constants.Constants.TREE_TALL:
            raise TreeNotTallException(cell.getIndex())

        if targetTree.isDormant():
            raise AlreadyActivatedTree(cell.getIndex())

        costOfGrowth: int = self._getGrowthCost(targetTree)
        currentSun: int = self.availableSun[player.getIndex()]
        if currentSun < costOfGrowth:
            raise NotEnoughSunException(costOfGrowth, player.getSun())

        self.availableSun[player.getIndex()] = currentSun - costOfGrowth
        self.dyingTrees.append(coord)
        targetTree.setDormant()

    def _getCostFor(self, size: int, owner: py.player.Player) -> int:
        baseCost: int = py.constants.Constants.TREE_BASE_COST[size]
        sameTreeCount: int = len(
            [
                t
                for t in self.trees.values()
                if (t.getSize() == size and t.getOwner() == owner)
            ]
        )  # CHECK
        return baseCost + sameTreeCount

    def _doSeed(self, player: py.player.Player, action: Action):
        targetCoord: py.cube_coord.CubeCoord = self._getCoordByIndex(
            action.getTargetId()
        )
        sourceCoord: py.cube_coord.CubeCoord = self._getCoordByIndex(
            action.getSourceId()
        )

        targetCell: py.cell.Cell = self.board.map[targetCoord]
        sourceCell: py.cell.Cell = self.board.map[sourceCoord]

        # check if the move is possible
        if self._aTreeIsOn(targetCell):
            raise CellNotEmptyException(targetCell.getIndex())
        sourceTree: py.tree.Tree = self.trees.get(sourceCell.getIndex(), None)
        if sourceTree is None:
            raise TreeNotFoundException(sourceCell.getIndex())
        if sourceTree.getSize() == py.constants.Constants.TREE_SEED:
            raise TreeIsSeedException(sourceCell.getIndex())
        if sourceTree.getOwner() != player:
            raise NotOwnerOfTreeException(sourceCell.getIndex(), sourceTree.getOwner())
        if sourceTree.isDormant():
            raise AlreadyActivatedTree(sourceCell.getIndex())
        distance: int = sourceCoord.distanceTo(targetCoord)
        if distance > sourceTree.getSize():
            raise TreeTooFarException(sourceCell.getIndex(), targetCell.getIndex())
        if targetCell.getRichness() == py.constants.Constants.RICHNESS_NULL:
            raise CellNotValidException(targetCell.getIndex())
        costOfSeed: int = self._getSeedCost(player)
        currentSun: int = self.availableSun[player.getIndex()]
        if currentSun < costOfSeed:
            raise NotEnoughSunException(costOfSeed, player.getSun())

        # the seed action is valid : do it
        self.availableSun[player.getIndex()] = currentSun - costOfSeed
        sourceTree.setDormant()
        seed: py.seed.Seed = py.seed.Seed()
        seed.setOwner(player.getIndex())
        seed.setSourceCell(sourceCell.getIndex())
        seed.setTargetCell(targetCell.getIndex())
        self.sentSeeds.append(seed)
        self._gameSummaryManager.addPlantSeed(player, targetCell, sourceCell)

    def _aTreeIsOn(self, cell: py.cell.Cell) -> bool:
        return cell.getIndex() in self.trees

    def _giveSun(self):
        givenToPlayer: List[int] = [None, None]

        for index, tree in self.trees.items():
            if (index not in self.shadows) or (
                self.shadows[index] < tree.getSize()
            ):  # CHECK
                owner: py.player.Player = tree.getOwner()
                owner.addSun(tree.getSize())
                givenToPlayer[owner.getIndex()] += tree.getSize()

        for player in self._gameManager.getPlayers():
            given: int = givenToPlayer[player.getIndex()]
            if given > 0:
                self._gameSummaryManager.addGather(player, given)

    def _removeDyingTrees(self):
        for coord in self.dyingTrees:
            cell: py.cell.Cell = self.board.map.get(coord)
            points: int = self.nutrients
            if cell.getRichness() == py.constants.Constants.RICHNESS_OK:
                points += py.constants.Constants.RICHNESS_BONUS_OK
            elif cell.getRichness() == py.constants.Constants.RICHNESS_LUSH:
                points += py.constants.Constants.RICHNESS_BONUS_LUSH

            player: py.player.Player = self.trees[cell.getIndex()].getOwner()
            player.addScore(points)
            self._gameManager.addTooltip(
                f"{player.getNicknameToken()} scores {points} points"
            )
            # self.trees.remove(cell.getIndex()) # CHECK trees in a dict
            del self.trees[cell.getIndex()]
            self._gameSummaryManager.addCutTree(player, cell, points)

    def _updateNutrients(self):
        # CHECK
        self.nutrients = max(0, self.nutrients - len(self.dyingTrees))

    def performGameUpdate(self):
        self.turn += 1

        if self.currentFrameType == py.frame_type.FrameType.GATHERING:
            self._gameSummaryManager.addRound(self.round)
            self.performSunGatheringUpdate()
            self.nextFrameType = py.frame_type.FrameType.ACTIONS

        elif self.currentFrameType == py.frame_type.FrameType.ACTIONS:
            self._gameSummaryManager.addRound(self.round)
            self.performActionUpdate()
            if self._allPlayersAreWaiting():
                self.nextFrameType = py.frame_type.FrameType.SUN_MOVE

        elif self.currentFrameType == py.frame_type.FrameType.SUN_MOVE:
            self._gameSummaryManager.addRoundTransition(self.round)
            self.performSunMoveUpdate()
            self.nextFrameType = py.frame_type.FrameType.GATHERING

        else:
            print(f"Error: {self.currentFrameType}", file=sys.stderr)

        self._gameManager.addToGameSummary(str(self._gameSummaryManager))
        self._gameSummaryManager.clear()

        if self._gameOver():
            self._gameManager.endGame()
        else:
            self._gameManager.setMaxTurns(self.turn + 1)

    def performSunMoveUpdate(self):
        self.round += 1
        if self.round < Game.MAX_ROUNDS:
            self.sun.move()
            if Game.ENABLE_SHADOW:
                self._calculateShadows()

        self._gameManager.setFrameDuration(
            py.constants.Constants.DURATION_SUNMOVE_PHASE
        )

    def performSunGatheringUpdate(self):
        # Wake players
        for player in self._gameManager.getPlayers():
            player.setWaiting(False)

        for index, tree in self.trees.items():
            tree.reset()

        # Harvest
        self._giveSun()

        self._gameManager.setFrameDuration(py.constants.Constants.DURATION_GATHER_PHASE)

    def performActionUpdate(self):

        for player in [p for p in self._gameManager.getPlayers() if not p.isWaiting()]:
            try:
                action: Action = player.getAction()
                if action.isGrow():
                    self._doGrow(player, action)
                elif action.isSeed():
                    self._doSeed(player, action)
                elif action.isComplete():
                    self._doComplete(player, action)
                else:
                    player.setWaiting(True)
                    self._gameSummaryManager.addWait(player)

            except GameException as e:
                self._gameSummaryManager.addError(
                    player.getNicknameToken() + ": " + str(e)
                )
                player.setWaiting(True)

        if self._seedsAreConflicting():
            self._gameSummaryManager.addSeedConflict(self.sentSeeds[0])
        else:
            for seed in self.sentSeeds:
                self._plantSeed(
                    self._gameManager.getPlayer(seed.getOwner()),
                    seed.getTargetCell(),
                    seed.getSourceCell(),
                )

            for player in self._gameManager.getPlayers():
                player.setSun(self.availableSun[player.getIndex()])

        self._removeDyingTrees()
        self._updateNutrients()
        self._gameManager.setFrameDuration(py.constants.Constants.DURATION_ACTION_PHASE)

    def _seedsAreConflicting(self) -> bool:
        return len(set([seed.getTargetCell() for seed in self.sentSeeds])) != len(
            self.sentSeeds
        )

    def _allPlayersAreWaiting(self) -> bool:
        return (
            len(
                [
                    player
                    for player in self._gameManager.getPlayers()
                    if player.isWaiting()
                ]
            )
            == self._gameManager.getPlayerCount()
        )

    def _plantSeed(self, player: py.player.Player, index: int, fatherIndex: int):
        seed: py.tree.Tree = self._placeTree(
            player, index, py.constants.Constants.TREE_SEED
        )
        seed.setDormant()
        seed.setFatherIndex(fatherIndex)

    def _placeTree(
        self, player: py.player.Player, index: int, size: int
    ) -> py.tree.Tree:
        tree: py.tree.Tree = py.tree.Tree()
        tree.setSize(size)
        tree.setOwner(player)
        self.trees[index] = tree
        return tree

    def onEnd(self):
        for player in self._gameManager.getActivePlayers():
            player.addScore(int(player.getSun() // 3))

        # if all the player have the same score, add +1 for each tree
        if (
            len(
                set(
                    [
                        player.getScore()
                        for player in self._gameManager.getActivePlayers()
                    ]
                )
            )
            == 1
        ):

            for index, tree in self.trees.items():
                if tree.getOwner().isActive():
                    tree.getOwner().addBonusScore(1)
                    tree.getOwner().addScore(1)

    def getBoard(self) -> Dict[py.cube_coord.CubeCoord, py.cell.Cell]:
        return self.board.map

    def getTrees(self) -> Dict[int, py.tree.Tree]:
        return self.trees

    def getShadows(self) -> Dict[int, int]:
        return self.shadows

    def _gameOver(self) -> bool:
        # CHECK
        return (self._gameManager.getActivePlayers().size() <= 1) or (
            self.round >= Game.MAX_ROUNDS
        )

    def getRound(self) -> int:
        return self.round

    def getTurn(self) -> int:
        return self.turn

    def getSun(self) -> py.sun.Sun:
        return self.sun

    def getNutrients(self) -> int:
        return self.nutrients

    def getCurrentFrameType(self) -> py.frame_type.FrameType:
        return self.currentFrameType

    def getSentSeeds(self) -> List[py.seed.Seed]:
        return self.sentSeeds
