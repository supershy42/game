from .arena import Arena
from arena.enums import Team
from arena.enums import Direction

class Bar:
    def __init__(self, arena: "Arena", team: Team):
        self.arena = arena
        self.team = team
        self.length = 6
        self.width = 1
        self.speed = 1
        self.x = 0
        self.y = 0
        self.reset()
        
    def move(self, direction: Direction):
        if direction == Direction.UP:
            self.y = max(self.y - self.speed, 0)
        elif direction == Direction.DOWN:
            self.y = min(self.y + self.speed, self.arena.height - self.length)

    def reset(self):
        self.y = (self.arena.height - self.length) // 2
        if self.team == Team.LEFT:
            self.x = 0
        elif self.team == Team.RIGHT:
            self.x = self.arena.width - self.width