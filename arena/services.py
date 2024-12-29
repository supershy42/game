from .models import NormalMatch
from django.db.models import Q
from django.db import IntegrityError, transaction
from datetime import datetime
import uuid

class ArenaService:
    @staticmethod
    def get_arena_group_name(arena_id):
        return f"arena_group_{arena_id}"

    @staticmethod
    def arena_websocket_url(arena_id):
        return f"/ws/arena/{arena_id}/"
    
    @staticmethod
    def generate_unique_id():
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{unique_id}_{timestamp}"
    
    @staticmethod
    def save_normal_match(result):
        try:
            with transaction.atomic():
                NormalMatch.objects.create(
                    unique_id=result['unique_id'],
                    left_player=result['left_player'],
                    right_player=result['right_player'],
                    left_player_score=result['left_player_score'],
                    right_player_score=result['right_player_score'],
                    winner=result['winner'],
                    state=NormalMatch.State.FINISHED,
                )
        except IntegrityError:
            pass
        
    @staticmethod
    def get_user_matches(user_id):
        matches = NormalMatch.objects.filter(
            Q(state=NormalMatch.State.FINISHED) &
            (Q(left_player=user_id) | Q(right_player=user_id))
        )
        return matches