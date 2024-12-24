from .arena import Arena
from arena.models import BaseMatch
from arena.enums import Direction

class Bar:
    def __init__(self, arena:"Arena", team:BaseMatch.Team):
        self.arena = arena
        self.team = team
        self.length = 6
        self.width = 1
        self.speed = 1
        self.x = 0
        self.y = 0
        self.margin = 3
        self.reset()
        
    def move(self, direction: Direction):
        if direction == Direction.UP:
            self.y = max(self.y - self.speed, 0)
        elif direction == Direction.DOWN:
            self.y = min(self.y + self.speed, self.arena.height - self.length)

    def reset(self):
        self.y = (self.arena.height - self.length) // 2
        if self.team == BaseMatch.Team.LEFT:
            self.x = 0 + self.margin
        elif self.team == BaseMatch.Team.RIGHT:
            self.x = self.arena.width - self.width - self.margin