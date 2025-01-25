from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .arena import Arena
    from .bar import Bar

from arena.models import BaseMatch

class Ball:
    def __init__(self, arena: "Arena"):
        self.arena = arena
        self.reset()
        self.speed = 3
        self.radius = 1
        
    def update_position(self):
        self.x += self.velocity["x"]
        self.y += self.velocity["y"]

    def reset(self):
        self.x = self.arena.width // 2  # 경기장 중앙
        self.y = self.arena.height // 2  # 경기장 중앙
        direction = 1 if self.arena.current_round % 2 == 1 else -1
        self.velocity = {"x": self.speed * direction, "y": self.speed * direction}
    
    def handle_collision(self, lbar: "Bar", rbar: "Bar"):
        if self.y - self.radius <= 0 or self.y + self.radius >= self.arena.height:
            self.velocity["y"] *= -1  # 위/아래 벽 충돌

        if self._check_bar_collision(lbar) or self._check_bar_collision(rbar):
            self.velocity["x"] *= -1
            
    def _check_bar_collision(self, bar: "Bar") -> bool:
        bounds = bar.get_collision_bounds()
        return (
            bounds["y1"] <= self.y <= bounds["y2"] and
            (
                bounds["x1"] <= self.x + self.radius or
                self.x - self.radius <= bounds["x2"]
            )
        )

    def check_boundary_collision(self):
        if self.x - self.radius <= 0:  # 왼쪽 벽 충돌
            return BaseMatch.Team.LEFT
        if self.x + self.radius >= self.arena.width:  # 오른쪽 벽 충돌
            return BaseMatch.Team.RIGHT
        return None
