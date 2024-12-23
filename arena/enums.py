from enum import Enum

class Team(Enum):
    LEFT = "left"
    RIGHT = "right"
    
class Direction(Enum):
    UP = "up"
    DOWN = "down"
    
class ArenaType(Enum):
    NORMAL = "normal"
    TOURNAMENT = "tournament"