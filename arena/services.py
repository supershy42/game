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
    def create_normal_match(unique_id, reception_id):
        try:
            with transaction.atomic():
                NormalMatch.objects.create(
                    unique_id=unique_id,
                    reception_id=reception_id,
                )
        except IntegrityError:
            pass
    
    @staticmethod
    def save_normal_match(match:NormalMatch, result):
        match.unique_id=result['arena_id']
        match.left_player=result['left_player']
        match.right_player=result['right_player']
        match.left_player_score=result['left_player_score']
        match.right_player_score=result['right_player_score']
        match.winner=result['winner']
        match.state=NormalMatch.State.FINISHED
        match.save()
        
    @staticmethod
    async def get_match(unique_id):
        return await NormalMatch.objects.aget(unique_id=unique_id)
        
    @staticmethod
    def get_user_matches(user_id):
        matches = NormalMatch.objects.filter(
            Q(state=NormalMatch.State.FINISHED) &
            (Q(left_player=user_id) | Q(right_player=user_id))
        )
        return matches