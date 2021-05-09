
#import java.util.ArrayList
#import java.util.Collections
#import java.util.HashMap
#import java.util.List
#import java.util.Map
#import java.util.Random
#import java.util.TreeMap
#import java.util.stream.Collectors
#import java.util.stream.Stream

from typing import List, Dict

from action.Action import Action
from exception.AlreadyActivatedTree import AlreadyActivatedTree
from exception.CellNotEmptyException import CellNotEmptyException
from exception.CellNotFoundException import CellNotFoundException
from exception.CellNotValidException import CellNotValidException
from exception.GameException import GameException
from exception.NotEnoughSunException import NotEnoughSunException
from exception.NotOwnerOfTreeException import NotOwnerOfTreeException
from exception.TreeAlreadyTallException import TreeAlreadyTallException
from exception.TreeIsSeedException import TreeIsSeedException
from exception.TreeNotFoundException import TreeNotFoundException
from exception.TreeNotTallException import TreeNotTallException
from exception.TreeTooFarException import TreeTooFarException

import com.codingame.gameengine.core.MultiplayerGameManager

#import com.google.inject.Inject
#import com.google.inject.Singleton
from java_compat import Singleton, Random

from Board import Board
from BoardGenerator import BoardGenerator
from Constants import Constants
from Config import Config
from CubeCoord import CubeCoord
from Seed import Seed
from Sun import Sun
from Tree import Tree
from Cell import Cell
from FrameType import FrameType

class Game(metaclass=Singleton):

    @Inject private MultiplayerGameManager<Player> gameManager
    @Inject private GameSummaryManager gameSummaryManager
    int nutrients = Config.STARTING_NUTRIENTS

    ENABLE_SEED : bool = None
    ENABLE_GROW : bool = None
    ENABLE_SHADOW : bool = None
    ENABLE_HOLES : bool = None
    MAX_ROUNDS : int = None
    STARTING_TREE_COUNT : int = None
    STARTING_TREE_SIZE : int = None
    STARTING_TREE_DISTANCE : int = None
    STARTING_TREES_ON_EDGES : bool = None

    board: Board
    trees: Dict[int, Tree] 
    dyingTrees: List[CubeCoord] 
    availableSun: List[int] 
    sentSeeds : List[Seed]
    sun : Sun
    shadows : Dict[int, int] 
    cells : List[Cell] 
    random : Random 
    round : int = 0
    turn : int = 0
    currentFrameType : FrameType = FrameType.INIT
    nextFrameType : FrameType = FrameType.GATHERING

    def init(self, seed: int):

        if gameManager.getLeagueLevel() == 1:
            # Wood 2
            MAX_ROUNDS = 1
            ENABLE_SEED = False
            ENABLE_GROW = False
            ENABLE_SHADOW = False
            ENABLE_HOLES = False
            STARTING_TREE_COUNT = 6
            STARTING_TREE_SIZE = Constants.TREE_TALL
            STARTING_TREE_DISTANCE = 0
            STARTING_TREES_ON_EDGES = False
          
        elif gameManager.getLeagueLevel() == 2:
            # Wood 1
            MAX_ROUNDS = 6
            ENABLE_SEED = False
            ENABLE_GROW = True
            ENABLE_SHADOW = False
            ENABLE_HOLES = False
            STARTING_TREE_COUNT = 4
            STARTING_TREE_SIZE = Constants.TREE_SMALL
            STARTING_TREE_DISTANCE = 1
            STARTING_TREES_ON_EDGES = False
            
        else:
            # Bronze+
            MAX_ROUNDS = Config.MAX_ROUNDS
            ENABLE_SEED = True
            ENABLE_GROW = True
            ENABLE_SHADOW = True
            ENABLE_HOLES = True
            STARTING_TREE_COUNT = Constants.STARTING_TREE_COUNT
            STARTING_TREE_SIZE = Constants.TREE_SMALL
            STARTING_TREE_DISTANCE = 2
            STARTING_TREES_ON_EDGES = True
        

        random = Random(seed)
        board = BoardGenerator.generate(random)
        trees = TreeMap<>()
        dyingTrees = list()
        cells = list()
        availableSun = ArrayList<>(gameManager.getPlayerCount())
        sentSeeds = list()
        self.initStartingTrees()

        sun = Sun()
        sun.setOrientation(0)

        shadows = dict()

        round = 0
        if ENABLE_SHADOW:
            self._calculateShadows()
        
    

    def getExpected(self) -> str:
        if not ENABLE_GROW and not ENABLE_SEED:
            return "COMPLETE <idx> | WAIT"
    
        if not ENABLE_SEED and ENABLE_GROW:
            return "GROW <idx> | COMPLETE <idx> | WAIT"
        
        return "SEED <from> <to> | GROW <idx> | COMPLETE <idx> | WAIT"
    

    def _getCoordByIndex(self, index: int) -> CubeCoord:
        for cubecoord, cell in board.map.items():
            if cell.getIndex() == index:
                return cubecoord
        raise CellNotFoundException(index)


    def initStartingTrees(self):

        startingCoords: List[CubeCoord] = ArrayList[CubeCoord]()
        if STARTING_TREES_ON_EDGES:
            startingCoords = self._getBoardEdges()
        else:
            startingCoords = ArrayList[CubeCoord](board.coords)
            startingCoords.removeIf(coord ->:
                return coord.getX() == 0 and coord.getY() == 0 and coord.getZ() == 0
            )
        

        startingCoords.removeIf(coord ->:
            Cell cell = board.map.get(coord)
            return cell.getRichness() == Constants.RICHNESS_NULL
        )
        List[CubeCoord] validCoords = ArrayList[CubeCoord]()

        while (validCoords.size() < STARTING_TREE_COUNT * 2):
            validCoords = self._tryInitStartingTrees(startingCoords)
        

        List<Player> players = gameManager.getPlayers()
        for (int i = 0 i < STARTING_TREE_COUNT i++):
            self._placeTree(players.get(0), board.map.get(validCoords.get(2 * i)).getIndex(), STARTING_TREE_SIZE)
            self._placeTree(players.get(1), board.map.get(validCoords.get(2 * i + 1)).getIndex(), STARTING_TREE_SIZE)
        
    

    def _tryInitStartingTrees(self, startingCoords: List[CubeCoord]) -> List[CubeCoord]: 
        List[CubeCoord] coordinates = ArrayList[CubeCoord]()

        List[CubeCoord] availableCoords = ArrayList<>(startingCoords)
        for (int i = 0 i < STARTING_TREE_COUNT i++):
            if (availableCoords.isEmpty()):
                return coordinates
            
            int r = random.nextInt(availableCoords.size())
            CubeCoord normalCoord = availableCoords.get(r)
            CubeCoord oppositeCoord = normalCoord.getOpposite()
            availableCoords.removeIf(coord ->:
                return coord.distanceTo(normalCoord) <= STARTING_TREE_DISTANCE or
                    coord.distanceTo(oppositeCoord) <= STARTING_TREE_DISTANCE
            )
            coordinates.add(normalCoord)
            coordinates.add(oppositeCoord)
        
        return coordinates
    

    def _calculateShadows(self):
        shadows.clear()
        trees.forEach((index, tree) ->:
            CubeCoord coord = board.coords.get(index)
            for (int i = 1 i <= tree.getSize() i++):
                CubeCoord tempCoord = coord.neighbor(sun.getOrientation(), i)
                if (board.map.containsKey(tempCoord)):
                    shadows.compute(
                        board.map.get(tempCoord).getIndex(),
                        (key, value) -> value == null ? tree.getSize() : max(value, tree.getSize())
                    )
                
            
        )
    

    def _getBoardEdges(self) -> List[CubeCoord]:
        centre: CubeCoord = CubeCoord(0, 0, 0)
        return board.coords.stream()
            .filter(coord -> coord.distanceTo(centre) == Config.MAP_RING_COUNT)
            .collect(Collectors.toList())
    

    def getCurrentFrameInfoFor(self, player: Player) -> List[str]:
        List[str] lines = list()
        lines.add(String.valueOf(round))
        lines.add(String.valueOf(nutrients))
        #Player information, receiving player first
        Player other = gameManager.getPlayer(1 - player.getIndex())
        lines.add(
            String.format(
                "%d %d",
                player.getSun(),
                player.getScore()
            )
        )
        lines.add(
            String.format(
                "%d %d %d",
                other.getSun(),
                other.getScore(),
                other.isWaiting() ? 1 : 0
            )
        )
        lines.add(String.valueOf(trees.size()))
        trees.forEach((index, tree) ->:
            lines.add(
                String.format(
                    "%d %d %d %d",
                    index,
                    tree.getSize(),
                    tree.getOwner() == player ? 1 : 0,
                    tree.isDormant() ? 1 : 0
                )
            )
        )

        List[str] possibleMoves = self._getPossibleMoves(player)
        lines.add(String.valueOf(possibleMoves.size()))
        possibleMoves
            .stream()
            .forEach(lines::add)

        return lines
    

    @staticmethod
    def _cubeAdd(a: CubeCoord, b: CubeCoord) -> CubeCoord:
        return CubeCoord(a.getX() + b.getX(), a.getY() + b.getY(), a.getZ() + b.getZ())
    

    def _getCoordsInRange(self, center: CubeCoord, N: int) -> List[CubeCoord]:
        results : List[CubeCoord] = list()
        for (int x = -N x <= +N x++):
            for (int y = max(-N, -x - N) y <= min(+N, -x + N) y++):
                z: int = -x - y
                results.add(Game._cubeAdd(center, CubeCoord(x, y, z)))
            
        return results
    

    def _getPossibleMoves(self, player: Player) -> List[str]:
        lines: List[str]  = list()
        lines.append("WAIT")

        possibleSeeds: List[str] = list()
        possibleGrows: List[str] = list()
        possibleCompletes: List[str] = list()

        if player.isWaiting():
            return lines
        

        #For each tree, where they can seed.
        #For each tree, if they can grow.
        int seedCost = self._getSeedCost(player)
        trees.entrySet()
            .stream()
            .filter(e -> e.getValue().getOwner() == player)
            .forEach(e ->:
                index: int = e.getKey()
                Tree tree = e.getValue()
                CubeCoord coord = board.coords.get(index)

                if (self._playerCanSeedFrom(player, tree, seedCost)):
                    for (CubeCoord targetCoord : self._getCoordsInRange(coord, tree.getSize())):
                        Cell targetCell = board.map.getOrDefault(targetCoord, Cell.NO_CELL)
                        if self._playerCanSeedTo(targetCell, player):
                            possibleSeeds.add(
                                String.format(
                                    "SEED %d %d",
                                    index,
                                    targetCell.getIndex()
                                )
                            )
                        
                    
                

                int growCost = self._getGrowthCost(tree)
                if (growCost <= player.getSun() and !tree.isDormant()):
                    if (tree.getSize() == Constants.TREE_TALL):
                        possibleCompletes.add(
                            String.format(
                                "COMPLETE %d",
                                index
                            )
                        )
                     else if (ENABLE_GROW):
                        possibleGrows.add(
                            String.format(
                                "GROW %d",
                                index
                            )
                        )
                    
                
            )

        Stream.of(possibleCompletes, possibleGrows, possibleSeeds)
            .forEach(possibleList ->:
                Collections.shuffle(possibleList, random)
                lines.addAll(possibleList)
            )

        return lines
    

    def _playerCanSeedFrom(self, player: Player, tree: Tree, seedCost: int) -> bool:
        return ENABLE_SEED and
            seedCost <= player.getSun() and
            tree.getSize() > Constants.TREE_SEED and
            !tree.isDormant()
    

    def playerCanSeedTo(self, targetCell: Cell, player: Player) -> bool:
        return targetCell.isValid() and
            (targetCell.getRichness() != Constants.RICHNESS_NULL) and
            (targetCell.getIndex() not in trees)
    

    def getGlobalInfoFor(self, player: Player) -> List[str]:
        lines: List[str] = list()
        lines.append(str(len(board.coords)))

        for coord: CubeCoord in board.coords:
            cell: Cell = board.map[coord]
            lines.append(f"{cell.getIndex()} {cell.getRichness()} {self._getNeighbourIds(coord)}")
        
        return lines
    

    def getNeighbourIds(self, coord: CubeCoord) -> str:
        orderedNeighborIds: List<int> = ArrayList<>(CubeCoord.directions.length)
        for (int i = 0 i < CubeCoord.directions.length ++i):
            orderedNeighborIds.add(
                board.map.getOrDefault(coord.neighbor(i), Cell.NO_CELL).getIndex()
            )
        
        return orderedNeighborIds.stream()
            .map(String::valueOf)
            .collect(Collectors.joining(" "))
    

    def resetGameTurnData(self):
        dyingTrees.clear()
        availableSun.clear()
        sentSeeds.clear()
        for (Player p : gameManager.getPlayers()):
            availableSun.add(p.getSun())
            p.reset()
        
        currentFrameType = nextFrameType
    

    def _getGrowthCost(self, targetTree: Tree) -> int:
        int targetSize = targetTree.getSize() + 1
        if (targetSize > Constants.TREE_TALL):
            return Constants.LIFECYCLE_END_COST
        
        return self._getCostFor(targetSize, targetTree.getOwner())
    

    def _getSeedCost(self, player: Player) -> int:
        return self._getCostFor(0, player)
    

    def _doGrow(self, player: Player, action: Action):
        CubeCoord coord = self._getCoordByIndex(action.getTargetId())
        Cell cell = board.map.get(coord)
        Tree targetTree = trees.get(cell.getIndex())

        if targetTree is None:
            raise TreeNotFoundException(cell.getIndex())
        
        if targetTree.getOwner() != player:
            raise NotOwnerOfTreeException(cell.getIndex(), targetTree.getOwner())
        
        if targetTree.isDormant():
            raise AlreadyActivatedTree(cell.getIndex())
        
        if targetTree.getSize() >= Constants.TREE_TALL:
            raise TreeAlreadyTallException(cell.getIndex())
        
        costOfGrowth: int = self._getGrowthCost(targetTree)
        currentSun: int = availableSun[player.getIndex()]
        if currentSun < costOfGrowth:
            raise NotEnoughSunException(costOfGrowth, player.getSun())
        

        availableSun.set(player.getIndex(), currentSun - costOfGrowth)

        targetTree.grow()
        gameSummaryManager.addGrowTree(player, cell)

        targetTree.setDormant()

    

    def _doComplete(self,player: Player, action: Action):
        coord: CubeCoord = self._getCoordByIndex(action.getTargetId())
        cell: Cell = board.map[coord]
        targetTree: Tree = trees.get(cell.getIndex(), None)
        if targetTree is None:
            raise TreeNotFoundException(cell.getIndex())
        
        if targetTree.getOwner() != player:
            raise NotOwnerOfTreeException(cell.getIndex(), targetTree.getOwner())
        
        if targetTree.getSize() < Constants.TREE_TALL:
            raise TreeNotTallException(cell.getIndex())
        
        if targetTree.isDormant():
            raise AlreadyActivatedTree(cell.getIndex())
        
        costOfGrowth: int = self._getGrowthCost(targetTree)
        currentSun: int = availableSun.get(player.getIndex())
        if (currentSun < costOfGrowth):
            raise NotEnoughSunException(costOfGrowth, player.getSun())
        
        availableSun[player.getIndex()] = currentSun - costOfGrowth
        dyingTrees.append(coord)
        targetTree.setDormant()

    

    def _getCostFor(self, size: int, owner: Player) -> int:
        int baseCost = Constants.TREE_BASE_COST[size]
        int sameTreeCount = (int) trees.values()
            .stream()
            .filter(t -> t.getSize() == size and t.getOwner() == owner)
            .count()
        return (baseCost + sameTreeCount)
    

    def _doSeed(self, player: Player, action:Action):
        targetCoord: CubeCoord = self._getCoordByIndex(action.getTargetId())
        sourceCoord: CubeCoord = self._getCoordByIndex(action.getSourceId())

        targetCell: Cell = board.map.get(targetCoord)
        sourceCell: Cell = board.map.get(sourceCoord)

        if self._aTreeIsOn(targetCell):
            raise CellNotEmptyException(targetCell.getIndex())
        
        Tree sourceTree = trees.get(sourceCell.getIndex())
        if (sourceTree == null):
            raise TreeNotFoundException(sourceCell.getIndex())
        
        if (sourceTree.getSize() == Constants.TREE_SEED):
            raise TreeIsSeedException(sourceCell.getIndex())
        
        if (sourceTree.getOwner() != player):
            raise NotOwnerOfTreeException(sourceCell.getIndex(), sourceTree.getOwner())
        
        if (sourceTree.isDormant()):
            raise AlreadyActivatedTree(sourceCell.getIndex())
        

        int distance = sourceCoord.distanceTo(targetCoord)
        if (distance > sourceTree.getSize()):
            raise TreeTooFarException(sourceCell.getIndex(), targetCell.getIndex())
        
        if (targetCell.getRichness() == Constants.RICHNESS_NULL):
            raise CellNotValidException(targetCell.getIndex())
        

        int costOfSeed = self._getSeedCost(player)
        int currentSun = availableSun.get(player.getIndex())
        if (currentSun < costOfSeed):
            raise NotEnoughSunException(costOfSeed, player.getSun())
        
        availableSun.set(player.getIndex(), currentSun - costOfSeed)
        sourceTree.setDormant()
        Seed seed = Seed()
        seed.setOwner(player.getIndex())
        seed.setSourceCell(sourceCell.getIndex())
        seed.setTargetCell(targetCell.getIndex())
        sentSeeds.add(seed)
        gameSummaryManager.addPlantSeed(player, targetCell, sourceCell)

    

    def _aTreeIsOn(self, cell: Cell) -> bool:
        return trees.containsKey(cell.getIndex())
    

    def _giveSun(self):
        givenToPlayer: List[int] = [None, None]
        trees.forEach((index, tree) ->:
            if (not shadows.containsKey(index) or shadows.get(index) < tree.getSize()):
                Player owner = tree.getOwner()
                owner.addSun(tree.getSize())
                givenToPlayer[owner.getIndex()] += tree.getSize()
            
        )
        gameManager.getPlayers().forEach(player ->:
            int given = givenToPlayer[player.getIndex()]
            if (given > 0):
                gameSummaryManager.addGather(player, given)
            
        )
    

    def _removeDyingTrees(self):
        dyingTrees.forEach(coord ->:
            Cell cell = board.map.get(coord)
            int points = nutrients
            if (cell.getRichness() == Constants.RICHNESS_OK):
                points += Constants.RICHNESS_BONUS_OK
             else if (cell.getRichness() == Constants.RICHNESS_LUSH):
                points += Constants.RICHNESS_BONUS_LUSH
            
            player: Player = trees.get(cell.getIndex()).getOwner()
            player.addScore(points)
            gameManager.addTooltip(
                player, String.format(
                    "%s scores %d points",
                    player.getNicknameToken(),
                    points
                )
            )
            trees.remove(cell.getIndex())
            gameSummaryManager.addCutTree(player, cell, points)
        )
    

    def _updateNutrients(self):
        dyingTrees.forEach(coord ->:
            nutrients = max(0, nutrients - 1)
        )
    

    def performGameUpdate(self):
        turn += 1

        if currentFrameType == FrameType.GATHERING:
            gameSummaryManager.addRound(round)
            performSunGatheringUpdate()
            nextFrameType = FrameType.ACTIONS
            
        elif currentFrameType == FrameType.ACTIONS:
            gameSummaryManager.addRound(round)
            performActionUpdate()
            if self._allPlayersAreWaiting():
                nextFrameType = FrameType.SUN_MOVE
            
        elif currentFrameType == FrameType.SUN_MOVE:
            gameSummaryManager.addRoundTransition(round)
            performSunMoveUpdate()
            nextFrameType = FrameType.GATHERING
            
        else:
            System.err.println("Error: " + currentFrameType)
            

        gameManager.addToGameSummary(str(gameSummaryManager))
        gameSummaryManager.clear()

        if self._gameOver():
            gameManager.endGame()
        else:
            gameManager.setMaxTurns(turn + 1)
        
    

    def performSunMoveUpdate(self):
        round += 1
        if (round < MAX_ROUNDS):
            sun.move()
            if (ENABLE_SHADOW):
                self._calculateShadows()
            
        
        gameManager.setFrameDuration(Constants.DURATION_SUNMOVE_PHASE)
    

    def performSunGatheringUpdate(self):
        # Wake players
        gameManager.getPlayers().forEach(p ->:
            p.setWaiting(False)
        )
        trees.forEach((index, tree) ->:
            tree.reset()
        )
        # Harvest
        self._giveSun()

        gameManager.setFrameDuration(Constants.DURATION_GATHER_PHASE)
    

    def performActionUpdate(self):
        gameManager.getPlayers()
            .stream()
            .filter(p -> !p.isWaiting())
            .forEach(player ->:
                try:
                    Action action = player.getAction()
                    if (action.isGrow()):
                        self._doGrow(player, action)
                    else if (action.isSeed()):
                        self._doSeed(player, action)
                    else if (action.isComplete()):
                        self._doComplete(player, action)
                    else:
                        player.setWaiting(True)
                        gameSummaryManager.addWait(player)
                    
                except GameException as e:
                    gameSummaryManager.addError(player.getNicknameToken() + ": " + e.getMessage())
                    player.setWaiting(True)
                
            )

        if self._seedsAreConflicting():
            gameSummaryManager.addSeedConflict(sentSeeds.get(0))
         else:
            sentSeeds.forEach(seed ->:
                self._plantSeed(gameManager.getPlayer(seed.getOwner()), seed.getTargetCell(), seed.getSourceCell())
            )
            for (player: Player : gameManager.getPlayers()):
                player.setSun(availableSun.get(player.getIndex()))
            
        
        self._removeDyingTrees()

        self._updateNutrients()

        gameManager.setFrameDuration(Constants.DURATION_ACTION_PHASE)

    

    def _seedsAreConflicting(self) -> bool:
        return sentSeeds.size() != sentSeeds
            .stream()
            .map(seed ->:
                return seed.getTargetCell()
            )
            .distinct()
            .count()
    

    def _allPlayersAreWaiting(self) -> bool:
        return gameManager.getPlayers()
            .stream()
            .filter(Player::isWaiting)
            .count() == gameManager.getPlayerCount()
    

    def _plantSeed(self, player: Player, index: int, fatherIndex: int):
        seed: Tree = self._placeTree(player, index, Constants.TREE_SEED)
        seed.setDormant()
        seed.setFatherIndex(fatherIndex)
    

    def _placeTree(self, player: Player, index: int, size: int) -> Tree:
        Tree tree = Tree()
        tree.setSize(size)
        tree.setOwner(player)
        trees[index] = tree
        return tree
    

    def onEnd(self):
        gameManager.getActivePlayers().forEach(
            player -> player.addScore(int(player.getSun() // 3))
        )
        if (
            gameManager.getActivePlayers().stream()
                .map(player -> player.getScore())
                .distinct()
                .count() == 1
        ):
            trees.forEach((index, tree) ->:
                if (tree.getOwner().isActive()):
                    tree.getOwner().addBonusScore(1)
                    tree.getOwner().addScore(1)
                
            )
        

    def getBoard(self) -> Dict[CubeCoord, Cell]:
        return board.map
    

    def getTrees(self) -> Dict[int, Tree]:
        return trees
    

    def getShadows(self) -> Dict[int, int]:
        return shadows
    

    def _gameOver(self) -> bool:
        return (gameManager.getActivePlayers().size() <= 1) or (round >= MAX_ROUNDS)
    

    def getRound(self) -> int:
        return round
    

    def getTurn(self) -> int:
        return turn
    

    def getSun(int) -> Sun:
        return sun
    

    def getNutrients(self) -> int:
        return nutrients
    

    def getCurrentFrameType(self) -> FrameType:
        return currentFrameType
    

    def getSentSeeds(self) -> List[Seed]:
        return sentSeeds
    

