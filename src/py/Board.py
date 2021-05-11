from typing import List, Dict

import py.cube_coord
import py.cell


class Board:
    def __init__(self, map: Dict[py.cube_coord.CubeCoord, py.cell.Cell]):

        self.map: Dict[py.cube_coord.CubeCoord, py.cell.Cell] = map

        self.coords: List[py.cube_coord.CubeCoord] = [
            cubecoord
            for (cubecoord, cell) in sorted(
                [(cubecoord, cell) for (cubecoord, cell) in map.items()],
                key=lambda item: item[1].getIndex(),
            )
        ]
