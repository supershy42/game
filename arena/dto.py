from config.redis_services import UserRedisService
from .models import BaseMatch
from asgiref.sync import async_to_sync
from datetime import datetime

class BaseMatchDTO:
    def __init__(self, match: BaseMatch, token):
        self.id = getattr(match, 'id', None)
        self.left_player = self._get_user(match.left_player, token)
        self.right_player = self._get_user(match.right_player, token)
        self.left_player_score = match.left_player_score
        self.right_player_score = match.right_player_score
        self.winner = self._get_user(match.winner, token)
        self.created_at = self._format_datetime(match.created_at)
        
    def to_dict(self):
        return {
            "id": self.id,
            "left_player": self.left_player,
            "right_player": self.right_player,
            "left_player_score": self.left_player_score,
            "right_player_score": self.right_player_score,
            "winner": self.winner,
            "created_at": self.created_at,
        }
        
    def _get_user(self, user_id, token):
        user = async_to_sync(UserRedisService.get_or_fetch_user_exclude_email)(user_id, token)
        return user
    
    def _format_datetime(self, dt):
        if isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return dt
        
class NormalMatchDTO(BaseMatchDTO):
    
    def __init__(self, match):
        super().__init__(match)

    def to_dict(self):
        base_dict = super().to_dict()
        return {
            **base_dict
        }