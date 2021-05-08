#import java.util.ArrayList
#import java.util.HashMap
#import java.util.List
#import java.util.Map
#import java.util.Random

from typing import Dict, List

from Board import Board
from CubeCoord import CubeCoord
from Cell import Cell
from Constants import Constants
from Config import Config
from Game import Game
from java_compat import Random

class BoardGenerator:

    board : Dict[CubeCoord, Cell]
    index : int

    @staticmethod
    def generateCell(coord: CubeCoord, richness: int):
        cell : Cell = Cell(BoardGenerator.index)
        cell.setRichness(richness)
        BoardGenerator.board[coord] = cell

        BoardGenerator.index += 1
    
    @staticmethod
    def generate(random: Random) -> Board:
        BoardGenerator.board = dict()
        BoardGenerator.index = 0

        centre : CubeCoord = CubeCoord(0, 0, 0)
        BoardGenerator.generateCell(centre, Constants.RICHNESS_LUSH)

        coord : CubeCoord = centre.neighbor(0)
        for distance in range(1, Config.MAP_RING_COUNT+1):
            for orientation in range(6):
                for count in range(distance):
                    if (distance == Config.MAP_RING_COUNT):
                        BoardGenerator.generateCell(coord, Constants.RICHNESS_POOR)
                    elif (distance == Config.MAP_RING_COUNT - 1):
                        BoardGenerator.generateCell(coord, Constants.RICHNESS_OK)
                    else:
                        BoardGenerator.generateCell(coord, Constants.RICHNESS_LUSH)
                    coord = coord.neighbor((orientation + 2) % 6)
            coord = coord.neighbor(0)
        
        coordList: List[CubeCoord] = list(BoardGenerator.board.keys())
        coordListSize : int = len(coordList)
        wantedEmptyCells: int = random.nextInt(Config.MAX_EMPTY_CELLS + 1) if Game.ENABLE_HOLES else 0
        actualEmptyCells: int = 0

        while (actualEmptyCells < wantedEmptyCells - 1):
            randIndex : int = random.nextInt(coordListSize)
            randCoord : CubeCoord = coordList.get(randIndex)
            if (BoardGenerator.board.get(randCoord).getRichness() != Constants.RICHNESS_NULL):
                BoardGenerator.board.get(randCoord).setRichness(Constants.RICHNESS_NULL)
                actualEmptyCells += 1
                if not randCoord.equals(randCoord.getOpposite()):
                    BoardGenerator.board.get(randCoord.getOpposite()).setRichness(Constants.RICHNESS_NULL)
                    actualEmptyCells += 1
        
        return Board(BoardGenerator.board)
