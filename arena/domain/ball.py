from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .arena import Arena
    from .bar import Bar

from arena.models import BaseMatch

class Ball:
    def __init__(self, arena: "Arena"):
        self.arena = arena
        self.x = arena.width // 2
        self.y = arena.height // 2
        self.speed = 3
        self.velocity = {"x": self.speed, "y": self.speed}
        self.radius = 1
        
    def update_position(self):
        self.x += self.velocity["x"]
        self.y += self.velocity["y"]

    def reset(self):
        self.x = self.arena.width // 2  # 경기장 중앙
        self.y = self.arena.height // 2  # 경기장 중앙
        if self.arena.current_round % 2 == 1:
            self.velocity = {"x": self.speed, "y": self.speed}
        else:
            self.velocity = {"x": self.speed * -1, "y": self.speed * -1}

    def handle_collision(self, lbar: "Bar", rbar: "Bar"):
        if self.y - self.radius <= 0 or self.y + self.radius >= self.arena.height:
            self.velocity["y"] *= -1  # 위/아래 벽 충돌

        if self._check_bar_collision(lbar) or self._check_bar_collision(rbar):
            self.velocity["x"] *= -1
            
    def _check_bar_collision(self, bar: "Bar") -> bool:
        bar_collosion_bounds = bar.get_collision_bounds()
        bar_x1 = bar_collosion_bounds["x1"]
        bar_x2 = bar_collosion_bounds["x2"]
        bar_y1 = bar_collosion_bounds["y1"]
        bar_y2 = bar_collosion_bounds["y2"]
        return (
            bar_x1 <= self.x + self.radius and
            bar_y1 <= self.y <= bar_y2
        ) or (
            self.x - self.radius <= bar_x2 and
            bar_y1 <= self.y <= bar_y2
        )

    def check_boundary_collision(self):
        if self.x - self.radius <= 0:  # 왼쪽 벽 충돌
            return BaseMatch.Team.LEFT
        if self.x + self.radius >= self.arena.width:  # 오른쪽 벽 충돌
            return BaseMatch.Team.RIGHT
        return None
