from typing import TYPE_CHECKING
from .ball import Ball
from arena.enums import Team
import asyncio
from config.consumer_utils import broadcast_event

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
        self.speed = 10
        self.group_name = None
        self.broadcast_func = None
    
    def set_messanger(self, group_name, broadcast_func):
        if self.group_name is None:
            self.group_name = group_name
        if self.broadcast_func is None:
            self.broadcast_func = broadcast_func
    
    async def add_player(self, player: "Player"):
        if not self.lp:
            player.set_team(Team.LEFT)
            self.lp = player
        elif not self.rp:
            player.set_team(Team.RIGHT)
            self.rp = player
        else:
            return None
        
        if self.lp and self.rp:
            await self.play()
        else:
            await self.broadcast_func('waiting', 'Waiting for other player.')
        
        return player.team
        
    async def remove_player(self, player: "Player"):
        if player is self.lp:
            self.lp = None
        elif player is self.rp:
            self.rp = None
            
    def is_started(self):
        return self._loop_task is not None
            
    async def play(self):
        if self._loop_task is None:
            self._loop_task = asyncio.create_task(self._game_loop())
            
    async def _game_loop(self):
        await self.start()
        await self.countdown()
        
        while not self.is_finished:
            self.ball.update_position()
            self.ball.handle_collision(self.lp.bar, self.rp.bar)

            round_result = self.check_round_end()
            if round_result:
                await self.broadcast_func('round.over', self.get_scores())
                self.reset_round()
                if self.check_winner():
                    break
                await self.countdown()

            await self.broadcast_func('state', self.get_state())
            await asyncio.sleep(1 / self.speed)
        
        await self.end_game()
        
    async def countdown(self):
        countdown = 3
        while countdown > 0:
            await self.broadcast_func('countdown', countdown)
            await asyncio.sleep(1)
            countdown -= 1
            
    async def start(self):
        await self.broadcast_func('start', 'Arena is starting!')
        
    async def end_game(self):
        self._loop_task = None
        winner = self.check_winner()
        if winner:
            arena_result = {
                'winner': winner.user_id,
                "lp_score": self.lp.score,
                "rp_score": self.rp.score,
                "lp_user_id": self.lp.user_id,
                "rp_user_id": self.rp.user_id,
                }
            await broadcast_event(self.group_name, 'arena.end', arena_result)
        
    def get_state(self):
        return {
            "ball": {"x": self.ball.x, "y": self.ball.y},
            "lp_bar": self.lp.bar.y,
            "rp_bar": self.rp.bar.y,
        }
    
    async def forfeit(self, exit_user_id):
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                if exit_user_id == self.lp.user_id:
                    self.lp.score = 0
                    self.rp.score = self.max_score
                elif exit_user_id == self.rp.user_id:
                    self.rp.score = 0
                    self.lp.score = self.max_score
                await self.end_game()
        
    def get_oppenent(self, user_id):
        if user_id == self.lp.user_id:
            return self.rp.user_id
        elif user_id == self.rp.user_id:
            return self.lp.user_id
        return None
        
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
    