from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .arena import Arena
from arena.enums import Team
from .bar import Bar

class Player:
    def __init__(self, user_id, arena: "Arena"):
        self.team:Team = None
        self.score = 0
        self.bar:Bar = Bar(arena, None)
        self.user_id = user_id
        
    def increment_score(self):
        self.score += 1
        
    def set_team(self, team:Team):
        self.team = team
        self.bar.team = team