
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
from Player import Player

class Game(metaclass=Singleton):

    @Inject private MultiplayerGameManager<Player> gameManager
    @Inject private GameSummaryManager gameSummaryManager
    nutrients: int = Config.STARTING_NUTRIENTS

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

        startingCoords: List[CubeCoord] = list()
        if STARTING_TREES_ON_EDGES:
            startingCoords = self._getBoardEdges()
        else:
            startingCoords = [coord for coord in board.coords if not(coord.getX()==0 and coord.getY()==0 and coord.getZ()==0)]
        

        validCoords: List[CubeCoord] = list()
        while (len(validCoords) < STARTING_TREE_COUNT * 2):
            validCoords = self._tryInitStartingTrees(startingCoords)
        

        players: List<Player> = gameManager.getPlayers()
        for i in range(STARTING_TREE_COUNT):
            self._placeTree(players[0], board.map.get(validCoords.get(2 * i)).getIndex(), STARTING_TREE_SIZE)
            self._placeTree(players[1], board.map.get(validCoords.get(2 * i + 1)).getIndex(), STARTING_TREE_SIZE)
        
    

    def _tryInitStartingTrees(self, startingCoords: List[CubeCoord]) -> List[CubeCoord]: 
        coordinates: List[CubeCoord] = list()

        for i in range(STARTING_TREE_COUNT):
 
            if not startingCoords:
                return coordinates
            
            r: int = random.nextInt(startingCoords.size())
            normalCoord: CubeCoord = startingCoords.get(r)
            oppositeCoord: CubeCoord = normalCoord.getOpposite()
            startingCoords.removeIf(coord ->:
                return coord.distanceTo(normalCoord) <= STARTING_TREE_DISTANCE or
                    coord.distanceTo(oppositeCoord) <= STARTING_TREE_DISTANCE
            )
            coordinates.append(normalCoord)
            coordinates.append(oppositeCoord)
        
        return coordinates
    

    def _calculateShadows(self):
        shadows.clear()
        for index, tree in trees.items(): 
            coord: CubeCoord = board.coords.get(index)
            for i in range(1, tree.getSize()+1):
                tempCoord: CubeCoord = coord.neighbor(sun.getOrientation(), i)
                if tempCoord in board.map:
                    key = board.map[tempCoord].getIndex()
                    value = max(shadows.get(key, tree.getSize()), tree.getSize())
                    shadows[key] = value 
                        

    def _getBoardEdges(self) -> List[CubeCoord]:
        centre: CubeCoord = CubeCoord(0, 0, 0)
        return [coord for coord in board.coords if coord.distanceTo(centre) == Config.MAP_RING_COUNT]

    def getCurrentFrameInfoFor(self, player: Player) -> List[str]:
        lines: List[str] = list()
        lines.append(str(round))
        lines.append(str(nutriments))

        #Player information, receiving player first
        other: Player = gameManager.getPlayer(1 - player.getIndex())
        lines.append(f"{player.getSun()} {player.getScore()}")
        lines.append(f"{other.getSun()} {other.getScore()} {1 if other.isWaiting() else 0}")
        lines.append(f"{len(trees)}")

        for index, tree in trees.items():
            lines.append(
                "{} {} {} {}".format(
                    index,
                    tree.getSize(),
                    1 if (tree.getOwner() == player) else 0,
                    1 if tree.isDormant() else 0
                )
            )
        
        possibleMoves: List[str] = self._getPossibleMoves(player)
        lines.append(str(len(possibleMoves)))
        for possiblemove in possibleMoves:
            lines.append(possiblemove)

        return lines
    

    @staticmethod
    def _cubeAdd(a: CubeCoord, b: CubeCoord) -> CubeCoord:
        return CubeCoord(a.getX() + b.getX(), a.getY() + b.getY(), a.getZ() + b.getZ())
    

    def _getCoordsInRange(self, center: CubeCoord, N: int) -> List[CubeCoord]:
        results : List[CubeCoord] = list()
        for x in range(-N, N+1):
            for y in range(max(-N, -x-N), min(+N, -x+N)+1):
                z: int = -x - y
                results.append(Game._cubeAdd(center, CubeCoord(x, y, z)))
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
        seedCost: int = self._getSeedCost(player)
        for index, tree in [(index, tree) for (index, tree) in trees.items() if tree.getOwner() == player]:
            coord: CubeCoord = board.coords.get(index)

            if self._playerCanSeedFrom(player, tree, seedCost):
                for targetCoord in self._getCoordsInRange(coord, tree.getSize()):
                    targetCell: Cell = board.map.get(targetCoord, Cell.NO_CELL)
                    if self._playerCanSeedTo(targetCell, player):
                        possibleSeeds.append(f"SEED {index} {targetCell.getIndex()}")
                    
                
            growCost: int = self._getGrowthCost(tree)
            if growCost <= player.getSun() and not tree.isDormant():
                if tree.getSize() == Constants.TREE_TALL:
                    possibleCompletes.append(f"COMPLETE {index}")
                elif ENABLE_GROW:
                    possibleGrows.append(f"GROW {index}")
                

        for possibleList in (possibleCompletes, possibleGrows, possibleSeeds):
            Collections.shuffle(possibleList, random)
            # CHECK
            lines.extend(possibleList)
            
        return lines
    

    def _playerCanSeedFrom(self, player: Player, tree: Tree, seedCost: int) -> bool:
        return ENABLE_SEED and
            (seedCost <= player.getSun()) and
            (tree.getSize() > Constants.TREE_SEED) and
            (not tree.isDormant())
    

    def playerCanSeedTo(self, targetCell: Cell, player: Player) -> bool:
        return targetCell.isValid() and
            (targetCell.getRichness() != Constants.RICHNESS_NULL) and
            (targetCell.getIndex() not in trees)
    

    def getGlobalInfoFor(self, player: Player) -> List[str]:
        lines: List[str] = list()
        lines.append(str(len(board.coords)))

        for coord in board.coords:
            cell: Cell = board.map[coord]
            lines.append(f"{cell.getIndex()} {cell.getRichness()} {self._getNeighbourIds(coord)}")
        
        return lines
    

    def getNeighbourIds(self, coord: CubeCoord) -> str:
        orderedNeighborIds: List<int> = [
            board.map.get(coord.neighbor(i), Cell.NO_CELL).getIndex()
            for i in range(len(CubeCoord.directions))
        ]
        return " ".join(orderedNeighborIds)
    

    def resetGameTurnData(self):
        dyingTrees.clear()
        availableSun.clear()
        sentSeeds.clear()
        for player in gameManager.getPlayers():
            availableSun.append(player.getSun())
            player.reset()
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

        for (index, tree) in trees.items():
            if (not shadows.containsKey(index) or shadows.get(index) < tree.getSize()):
                owner: Player = tree.getOwner()
                owner.addSun(tree.getSize())
                givenToPlayer[owner.getIndex()] += tree.getSize()
            
        
        for player in gameManager.getPlayers():
            given: int = givenToPlayer[player.getIndex()]
            if (given > 0):
                gameSummaryManager.addGather(player, given)
            
        
    

    def _removeDyingTrees(self):
        for coord in dyingTrees:
            cell: Cell = board.map.get(coord)
            points: int = nutrients
            if cell.getRichness() == Constants.RICHNESS_OK:
                points += Constants.RICHNESS_BONUS_OK
             elif cell.getRichness() == Constants.RICHNESS_LUSH:
                points += Constants.RICHNESS_BONUS_LUSH
            
            player: Player = trees.get(cell.getIndex()).getOwner()
            player.addScore(points)
            gameManager.addTooltip(f"{player.getNicknameToken()} scores {points} points")
            trees.remove(cell.getIndex())
            gameSummaryManager.addCutTree(player, cell, points)
    
    
    def _updateNutrients(self):
        # CHECK
        nutrients = max(0, nutrients - len(dyingTrees))
        
    
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
        for player in gameManager.getPlayers():
            player.setWaiting(False)
        
        for index, tree in trees.items():
            tree.reset()
        
        # Harvest
        self._giveSun()

        gameManager.setFrameDuration(Constants.DURATION_GATHER_PHASE)
    

    def performActionUpdate(self):

        for player in [p for p in gameManager.getPlayers() if not p.isWaiting()]:
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
                    gameSummaryManager.addWait(player)
                
            except GameException as e:
                gameSummaryManager.addError(player.getNicknameToken() + ": " + str(e))
                player.setWaiting(True)
                

        if self._seedsAreConflicting():
            gameSummaryManager.addSeedConflict(sentSeeds.get(0))
        else:
            for seed in sentSeeds:
                self._plantSeed(
                    gameManager.getPlayer(seed.getOwner()), 
                    seed.getTargetCell(), 
                    seed.getSourceCell()
                )
            
            for player in gameManager.getPlayers():
                player.setSun(availableSun.get(player.getIndex()))
        
        self._removeDyingTrees()
        self._updateNutrients()
        gameManager.setFrameDuration(Constants.DURATION_ACTION_PHASE)

    

    def _seedsAreConflicting(self) -> bool:
        return len(set([seed.getTargetCell() for seed in sentSeeds])) != sentSeeds
    

    def _allPlayersAreWaiting(self) -> bool:
        return len([player for player in gameManager.getPlayers() if player.isWaiting()]) == gameManager.getPlayerCount()
    

    def _plantSeed(self, player: Player, index: int, fatherIndex: int):
        seed: Tree = self._placeTree(player, index, Constants.TREE_SEED)
        seed.setDormant()
        seed.setFatherIndex(fatherIndex)
    

    def _placeTree(self, player: Player, index: int, size: int) -> Tree:
        tree: Tree = Tree()
        tree.setSize(size)
        tree.setOwner(player)
        trees[index] = tree
        return tree
    

    def onEnd(self):
        for player in gameManager.getActivePlayers():
            player.addScore(int(player.getSun() // 3))

        # if all the player have the same score, add +1 for each tree
        if len(set([ player.getScore() for player in gameManager.getActivePlayers() ])) == 1:

            for (index, tree) in trees.items():
                if tree.getOwner().isActive():
                    tree.getOwner().addBonusScore(1)
                    tree.getOwner().addScore(1)
        

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
    

