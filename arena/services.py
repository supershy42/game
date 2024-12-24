from .models import BaseMatch

class ArenaService:
    @staticmethod
    def get_arena_group_name(arena_id):
        return f"arena_{arena_id}"

    @staticmethod
    def arena_websocket_url(arena_id):
        return f"/ws/arena/{arena_id}/"
    
    @staticmethod
    async def save_match(result):
        await BaseMatch.objects.acreate(
            left_player=result['left_player'],
            right_player=result['right_player'],
            left_player_score=result['left_player_score'],
            right_player_score=result['right_player_score'],
            winner=result['winner'],
            state=BaseMatch.State.FINISHED,
        )