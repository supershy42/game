from arena.enums import Team
from .bar import Bar
from .arena import Arena

class Player:
    def __init__(self, team:Team, arena:Arena):
        self.team = team
        self.score = 0
        self.bar = Bar(self)
        self.arena = arena
        
    def increment_score(self):
        self.score += 1