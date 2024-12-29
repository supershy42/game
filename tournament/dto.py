from arena.dto import BaseMatchDTO
from .models import TournamentMatch, Tournament
from config.redis_services import UserRedisService
from asgiref.sync import async_to_sync
from datetime import datetime


class TournamentMatchDTO(BaseMatchDTO):
    def __init__(self, match: TournamentMatch, token):
        super().__init__(match, token)
        self.round = match.round.round_number
        self.match_number = match.match_number
        self.state = match.state

    def to_dict(self):
        base_dict = super().to_dict()
        return {
            **base_dict,
            "round": self.round,
            "match_number": self.match_number,
            "state": self.state,
        }
        

class TournamentDTO():
    def __init__(self, tournament: Tournament, token):
        self.id = getattr(tournament, 'id', None)
        self.name = tournament.name
        self.max_participants = tournament.max_participants
        self.winner = self._get_user(tournament.winner, token)
        self.creator = self._get_user(tournament.creator, token)
        self.state = tournament.state
        self.current_participants = tournament.current_participants
        self.total_rounds = tournament.total_rounds
        self.created_at = self._format_datetime(tournament.created_at)
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "max_participants": self.max_participants,
            "winner": self.winner,
            "creator": self.creator,
            "state": self.state,
            "current_participants": self.current_participants,
            "total_rounds": self.total_rounds,
            "created_at": self.created_at,
        }
        
    def _get_user(self, user_id, token):
        user = async_to_sync(UserRedisService.get_or_fetch_user_exclude_email)(user_id, token)
        return user
    
    def _format_datetime(self, dt):
        if isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return dt