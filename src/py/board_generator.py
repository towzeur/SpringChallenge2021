from typing import Dict, List

from py.java.compat import Random

import py.board
import py.cube_coord
import py.cell
import py.constants
import py.config
import py.game


class BoardGenerator:

    board: Dict[py.cube_coord.CubeCoord, py.cell.Cell]
    index: int

    @staticmethod
    def generateCell(coord: py.cube_coord.CubeCoord, richness: int):
        cell: py.cell.Cell = py.cell.Cell(BoardGenerator.index)
        cell.setRichness(richness)
        BoardGenerator.board[coord] = cell

        BoardGenerator.index += 1

    @staticmethod
    def generate(random: Random) -> py.board.Board:
        BoardGenerator.board = dict()
        BoardGenerator.index = 0

        centre: py.cube_coord.CubeCoord = py.cube_coord.CubeCoord(0, 0, 0)
        BoardGenerator.generateCell(centre, py.constants.Constants.RICHNESS_LUSH)

        # construct the map ring by ring
        coord: py.cube_coord.CubeCoord = centre.neighbor(0)
        for distance in range(1, py.config.Config.MAP_RING_COUNT + 1):
            for orientation in range(6):
                for count in range(distance):
                    if distance == py.config.Config.MAP_RING_COUNT:
                        BoardGenerator.generateCell(
                            coord, py.constants.Constants.RICHNESS_POOR
                        )
                    elif distance == py.config.Config.MAP_RING_COUNT - 1:
                        BoardGenerator.generateCell(
                            coord, py.constants.Constants.RICHNESS_OK
                        )
                    else:
                        BoardGenerator.generateCell(
                            coord, py.constants.Constants.RICHNESS_LUSH
                        )
                    coord = coord.neighbor((orientation + 2) % 6)
            coord = coord.neighbor(0)

        # create the desired number of Empty Cells
        coordList: List[py.cube_coord.CubeCoord] = list(BoardGenerator.board.keys())
        coordListSize: int = len(coordList)
        wantedEmptyCells: int = (
            random.nextInt(py.config.Config.MAX_EMPTY_CELLS + 1)
            if py.game.Game.ENABLE_HOLES
            else 0
        )
        actualEmptyCells: int = 0
        while actualEmptyCells < wantedEmptyCells - 1:
            randIndex: int = random.nextInt(coordListSize)
            randCoord: py.cube_coord.CubeCoord = coordList[randIndex]
            if (
                BoardGenerator.board[randCoord].getRichness()
                != py.constants.Constants.RICHNESS_NULL
            ):
                BoardGenerator.board[randCoord].setRichness(
                    py.constants.Constants.RICHNESS_NULL
                )
                actualEmptyCells += 1
                if not randCoord.equals(randCoord.getOpposite()):
                    BoardGenerator.board[randCoord.getOpposite()].setRichness(
                        py.constants.Constants.RICHNESS_NULL
                    )
                    actualEmptyCells += 1

        return py.board.Board(BoardGenerator.board)
