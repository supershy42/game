from typing import TYPE_CHECKING
from .ball import Ball
from arena.enums import Team
import asyncio

if TYPE_CHECKING:
    from .player import Player
    

class Arena:
    def __init__(self):
        self.width = 138
        self.height = 76
        self.lp = None
        self.rp = None
        self.ball = Ball(self)
        self.current_round = 1
        self.max_score = 3
        self._loop_task = None
        self.is_finished = False
        
    async def add_player(self, player: "Player", broadcast_func):
        if not self.lp:
            player.set_team(Team.LEFT)
            self.lp = player
            await broadcast_func('waiting', 'Waiting for other player.')
            return Team.LEFT
        elif not self.rp:
            player.set_team(Team.RIGHT)
            self.rp = player
            await self.play(broadcast_func)
            return Team.RIGHT
            
    async def play(self, broadcast_func):
        if self._loop_task is None:
            self._loop_task = asyncio.create_task(self._game_loop(broadcast_func))
            
    async def _game_loop(self, broadcast_func):
        await self.start(broadcast_func)
        await self.countdown(broadcast_func)
        
        while not self.is_finished:
            self.ball.update_position()
            self.ball.handle_collision(self.lp.bar, self.rp.bar)

            round_result = self.check_round_end()
            if round_result:
                await broadcast_func('round.over', self.get_scores())
                self.reset_round()
                if self.check_winner():
                    break
                await self.countdown(broadcast_func)

            await broadcast_func('update', self.get_state())
            await asyncio.sleep(1)
        
        await self.end_game(broadcast_func)
        
    async def countdown(self, broadcast_func):
        countdown = 3
        while countdown > 0:
            await broadcast_func('countdown', countdown)
            await asyncio.sleep(1)
            countdown -= 1
            
    async def start(self, broadcast_func):
        print("start!!")
        await broadcast_func('start', 'Arena is starting!')
        
    async def end_game(self, broadcast_func):
        print("Arena ended.")
        winner = self.check_winner()
        if winner:
            await broadcast_func('end', {'winner': winner.user_id})
        
    def get_state(self):
        return {
            "ball": {"x": self.ball.x, "y": self.ball.y},
            "lp_bar": self.lp.bar.y,
            "rp_bar": self.rp.bar.y,
        }
        
    def get_scores(self):
        return {
            "lp_score": self.lp.score,
            "rp_score": self.rp.score,
        }
    
    def reset_round(self):
        self.current_round += 1
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
    