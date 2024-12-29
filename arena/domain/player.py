from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .arena import Arena
from arena.models import BaseMatch
from .bar import Bar
from arena.enums import Direction

class Player:
    def __init__(self, user_id, arena: "Arena", team:BaseMatch.Team):
        self.team:BaseMatch.Team = team
        self.score = 0
        self.bar:Bar = Bar(arena, None)
        self.user_id = user_id
        
    def increment_score(self):
        self.score += 1
        
    def set_team(self, team:BaseMatch.Team):
        self.team = team
        self.bar.team = team
        
    def move(self, direction:Direction):
        self.bar.move(direction)