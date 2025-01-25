from typing import TYPE_CHECKING
from .ball import Ball
from arena.models import BaseMatch
import asyncio
from config.consumer_utils import broadcast_event

if TYPE_CHECKING:
    from .player import Player
    

class Arena:
    def __init__(self, arena_id):
        self.arena_id = arena_id
        self.width = 138
        self.height = 76
        self.left_player = None
        self.right_player = None
        self.ball = Ball(self)
        self.current_round = 1
        self.max_score = 2
        self._loop_task = None
        self.is_finished = False
        self.speed = 5
        self.group_name = None
        self.broadcast_func = None
    
    def set_messenger(self, group_name, broadcast_func):
        if self.group_name is None:
            self.group_name = group_name
        if self.broadcast_func is None:
            self.broadcast_func = broadcast_func
            
    def get_remaining_team(self):
        if not self.left_player:
            return BaseMatch.Team.LEFT
        elif not self.right_player:
            return BaseMatch.Team.RIGHT
    
    async def add_player(self, player: "Player"):
        team = player.team
        if not self.left_player and team == BaseMatch.Team.LEFT:
            self.left_player = player
        elif not self.right_player and team == BaseMatch.Team.RIGHT:
            self.right_player = player
        else:
            return
        
        if self.left_player and self.right_player:
            await self.play()
        else:
            await self.broadcast_func('waiting', 'Waiting for other player.')
        
        return player.team
        
    async def remove_player(self, player: "Player"):
        if player is self.left_player:
            self.left_player = None
        elif player is self.right_player:
            self.right_player = None
            
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
            self.ball.handle_collision(self.left_player.bar, self.right_player.bar)

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
                "arena_id": self.arena_id,
                "winner": winner.user_id,
                "left_player_score": self.left_player.score,
                "right_player_score": self.right_player.score,
                "left_player": self.left_player.user_id,
                "right_player": self.right_player.user_id,
                }
            await broadcast_event(self.group_name, 'arena.end', arena_result)
        
    def get_state(self):
        return {
            "ball": {"x": self.ball.x, "y": self.ball.y},
            "left_player_bar": self.left_player.bar.y,
            "right_player_bar": self.right_player.bar.y,
        }
    
    async def forfeit(self, exit_user_id):
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                if exit_user_id == self.left_player.user_id:
                    self.left_player.score = 0
                    self.right_player.score = self.max_score
                elif exit_user_id == self.right_player.user_id:
                    self.right_player.score = 0
                    self.left_player.score = self.max_score
                await self.end_game()
        
    def get_oppenent(self, user_id):
        if user_id == self.left_player.user_id:
            return self.right_player.user_id
        elif user_id == self.right_player.user_id:
            return self.left_player.user_id
        return None
        
    def get_scores(self):
        return {
            "left_player_score": self.left_player.score,
            "right_player_score": self.right_player.score,
        }
    
    def reset_round(self):
        self.current_round += 1
        self.ball.reset()
        self.left_player.bar.reset()
        self.right_player.bar.reset()
        
    def check_winner(self):
        if self.left_player.score >= self.max_score:
            self.is_finished = True
            return self.left_player
        if self.right_player.score >= self.max_score:
            self.is_finished = True
            return self.right_player
        return None

    def check_round_end(self):
        result = self.ball.check_boundary_collision()
        if result == BaseMatch.Team.LEFT:
            self.right_player.increment_score()
        elif result == BaseMatch.Team.RIGHT:
            self.left_player.increment_score()
        return result
    