from typing import List, Dict

from CubeCoord import CubeCoord
from Cell import Cell

# import java.util.List;
# import java.util.Map;
# import java.util.Map.Entry;
# import java.util.stream.Collectors;


class Board:
    def __init__(self, map: Dict[CubeCoord, Cell]):
        self.map: Dict[CubeCoord, Cell] = map

        self.coords: List[CubeCoord] = [
            cubecoord
            for cubecoord, cell in sorted(
                [(cubecoord, cell) for (cubecoord, cell) in map.items()],
                key=lambda cubecoord, cell: cell.getIndex(),
            )
        ]
