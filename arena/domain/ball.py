from .bar import Bar
from .arena import Arena
from arena.enums import Team

class Ball:
    def __init__(self, arena: Arena):
        self.arena = arena
        self.x = arena.width // 2
        self.y = arena.height // 2
        self.velocity = {"x": 1, "y": 1}
        self.radius = 1
        
    def update_position(self):
        self.x += self.velocity["x"]
        self.y += self.velocity["y"]

    def reset(self):
        self.x = self.arena.width // 2  # 경기장 중앙
        self.y = self.arena.height // 2  # 경기장 중앙
        if self.arena.current_round % 2 == 1:
            self.velocity = {"x": 1, "y": 1}
        else:
            self.velocity = {"x": -1, "y": -1}

    def handle_collision(self, bar: Bar):
        if self.y - self.radius <= 0 or self.y + self.radius >= self.arena.height:
            self.velocity["y"] *= -1  # 위/아래 벽 충돌

        if (
            bar.player.team == Team.LEFT
            and self.x - self.radius <= bar.x + bar.width
            and bar.y <= self.y <= bar.y + bar.length
        ):
            self.velocity["x"] *= -1  # 왼쪽 바 충돌
        elif (
            bar.player.team == Team.RIGHT
            and self.x + self.radius >= bar.x
            and bar.y <= self.y <= bar.y + bar.length
        ):
            self.velocity["x"] *= -1  # 오른쪽 바 충돌

    def check_boundary_collision(self):
        if self.x - self.radius <= 0:  # 왼쪽 벽 충돌
            return Team.LEFT
        if self.x + self.radius >= self.arena.width:  # 오른쪽 벽 충돌
            return Team.RIGHT
        return None
