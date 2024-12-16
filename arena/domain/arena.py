from .ball import Ball
from .player import Player
from arena.enums import Team

class Arena:
    def __init__(self, lp:Player, rp:Player):
        self.width = 138
        self.height = 76
        self.lp = lp
        self.rp = rp
        self.ball = Ball(self)
        self.current_round = 1
        self.max_score = 5
        self.is_finished = False
        
    def reset_round(self):
        self.ball.reset()
        self.lp.bar.reset()
        self.rp.bar.reset()
        
    def check_winner(self):
        if self.lp.score >= self.max_score:
            self.is_finished = True
            return self.lp
        if self.rp.score >= self.max_score:
            self.is_finished = True
            return self.rp
        return None

    def check_round_end(self):
        result = self.ball.check_boundary_collision()
        if result == Team.LEFT:
            self.rp.increment_score()
        elif result == Team.RIGHT:
            self.lp.increment_score()
        return result
    