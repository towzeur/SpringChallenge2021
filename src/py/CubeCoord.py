#package com.codingame.game;

#import com.codingame.view.Serializer;

class CubeCoord:

    directions = (
        ( 1, -1,  0 ), 
        ( +1, 0, -1 ), 
        ( 0, +1, -1 ), 
        ( -1, +1, 0 ), 
        ( -1, 0, +1 ), 
        ( 0, -1, +1 ) 
    )

    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z
    
    def getX(self) -> int:
        return self.x

    def getY(self) -> int:
        return self.y
    
    def getZ(self) -> int:
        return self.z
    
    def hashCode(self):
        prime : int = 31
        result : int = 1
        result = prime * result + self.x
        result = prime * result + self.y
        result = prime * result + self.z
        return result
    

    def equals(self, obj) -> bool:
        if self == obj:
            return True
        if not isinstance(obj, CubeCoord):
            return False
        return (self.x == obj.x) and (self.y == obj.y) and (self.z == obj.z)
    

    def neighbor(self, orientation: int, distance: int = 1) -> 'CubeCoord':
        nx: int = self.x + CubeCoord.directions[orientation][0] * distance
        ny: int = self.y + CubeCoord.directions[orientation][1] * distance
        nz: int = self.z + CubeCoord.directions[orientation][2] * distance
        return CubeCoord(nx, ny, nz)
    

    def distanceTo(self, dst : 'CubeCoord') -> int:
        return (abs(self.x - dst.x) + abs(self.y - dst.y) + abs(self.z - dst.z)) // 2
    

    def __str__(self):
        return f"{self.x} {self.y} {self.z}"
    

    def getOpposite(self) -> 'CubeCoord':
        return CubeCoord(-self.x, -self.y, -self.z)
    

