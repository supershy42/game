from .arena import Arena
from arena.models import BaseMatch
from arena.enums import Direction

class Bar:
    def __init__(self, arena:"Arena", team:BaseMatch.Team):
        self.arena = arena
        self.team = team
        self.width = 2
        self.height = 10
        self.x_radius = self.width / 2
        self.y_radius = self.height / 2
        self.speed = 1
        self.margin = 3
        self.reset()
        
    def move(self, direction: Direction):
        if direction == Direction.UP:
            self.y = max(self.y - self.speed, 0 + self.y_radius)
        elif direction == Direction.DOWN:
            self.y = min(self.y + self.speed, self.arena.height - self.y_radius)

    def reset(self):
        self.y = self.arena.height // 2
        if self.team == BaseMatch.Team.LEFT:
            self.x = 0 + self.x_radius + self.margin
        else:
            self.x = self.arena.width - self.x_radius - self.margin    
    
    def get_collision_bounds(self):
        return {
            "x1": self.x - self.x_radius,
            "x2": self.x + self.x_radius,
            "y1": self.y - self.y_radius,
            "y2": self.y + self.y_radius,
        }