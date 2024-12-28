import redis.asyncio as redis
import json
from django.conf import settings

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

class ReceptionRedisService:
    @staticmethod
    def get_participants_key(reception_id):
        return f'reception_{reception_id}_participants'

    @staticmethod
    def get_user_reception_key(user_id):
        return f'user_{user_id}_reception'

    @staticmethod
    def get_invitation_key(reception_id, user_id):
        return f'invitation:{reception_id}:{user_id}'
    
    @staticmethod
    def get_allowed_users_key(reception_id):
        return f"reception:{reception_id}:allowed_users"

    @staticmethod
    def get_playing_reception_key():
        return 'playing_reception'
    
    @staticmethod
    def get_partial_detail(user_detail):
        return {
            "user_id": str(user_detail["id"]),
            "nickname": user_detail["nickname"],
            "avatar": user_detail["avatar"],
            "is_ready": 0
        }

    @staticmethod
    async def add_user(reception_id, user_id, token):
        participants_key = ReceptionRedisService.get_participants_key(reception_id)
        user_reception_key = ReceptionRedisService.get_user_reception_key(user_id)
        
        if await redis_client.hexists(participants_key, user_id):
            return False
        
        user_detail = await UserRedisService.get_or_fetch_user(user_id, token)
        if not user_detail:
            return False
        
        partial_detail = ReceptionRedisService.get_partial_detail(user_detail)
        
        await redis_client.hset(participants_key, user_id, json.dumps(partial_detail))
        await redis_client.set(user_reception_key, reception_id)
        return True

    @staticmethod    
    async def remove_user(reception_id, user_id):    
        participants_key = ReceptionRedisService.get_participants_key(reception_id)
        await redis_client.hdel(participants_key, user_id)
        
        user_reception_key = ReceptionRedisService.get_user_reception_key(user_id)
        await redis_client.delete(user_reception_key)
        
    @staticmethod
    async def toggle_ready(reception_id, user_id):
        participants_key = ReceptionRedisService.get_participants_key(reception_id)
        raw_data = await redis_client.hget(participants_key, user_id)
        if raw_data:
            user_detail = json.loads(raw_data.decode())
            current_ready_state = user_detail.get("is_ready", 0)
            new_ready_state = 0 if current_ready_state == 1 else 1
            user_detail["is_ready"] = new_ready_state
            await redis_client.hset(participants_key, user_id, json.dumps(user_detail))

    @staticmethod    
    async def should_remove(reception_id):
        participants = await ReceptionRedisService.get_participants(reception_id)

        if len(participants) < 1:
            return True
        return False

    @staticmethod    
    async def should_start(reception_id):
        participants = await ReceptionRedisService.get_participants(reception_id)

        if len(participants) > 1:
            return all(p["is_ready"] == 1 for p in participants)
        return False

    @staticmethod
    async def get_participants(reception_id):
        participants_key = ReceptionRedisService.get_participants_key(reception_id)
        raw_map = await redis_client.hgetall(participants_key)
        
        participants = []
        for _, v in raw_map.items():
            user_detail = json.loads(v.decode())
            participants.append(user_detail)
        return participants

    @staticmethod
    async def get_current_reception(user_id):
        user_reception_key = ReceptionRedisService.get_user_reception_key(user_id)
        reception_id = await redis_client.get(user_reception_key)
        if reception_id is not None:
            reception_id = reception_id.decode()
        return reception_id

    @staticmethod
    async def is_invited(reception_id, user_id):
        invitation_key = ReceptionRedisService.get_invitation_key(reception_id, user_id)
        return await redis_client.get(invitation_key) is not None

    @staticmethod
    async def set_invitation(reception_id, user_id, ttl=3000): # 일단 300초
        invitation_key = ReceptionRedisService.get_invitation_key(reception_id, user_id)
        await redis_client.setex(invitation_key, ttl, 1)
        
    @staticmethod
    async def add_allowed_user(reception_id, user_id):
        key = ReceptionRedisService.get_allowed_users_key(reception_id)
        await redis_client.sadd(key, user_id)
        
    @staticmethod
    async def is_allowed_user(reception_id, user_id):
        key = ReceptionRedisService.get_allowed_users_key(reception_id)
        return await redis_client.sismember(key, user_id)
        
    @staticmethod
    async def remove_allowed_user(reception_id, user_id):
        key = ReceptionRedisService.get_allowed_users_key(reception_id)
        await redis_client.srem(key, user_id)

    @staticmethod
    async def set_playing(reception_id):
        key = ReceptionRedisService.get_playing_reception_key()
        await redis_client.sadd(key, reception_id)

    @staticmethod
    async def is_playing(reception_id):
        key = ReceptionRedisService.get_playing_reception_key()
        return await redis_client.sismember(key, reception_id)

    @staticmethod
    async def unset_playing(reception_id):
        key = ReceptionRedisService.get_playing_reception_key()
        await redis_client.srem(key, reception_id)
        

class UserRedisService:
    @staticmethod
    def get_channel_name_key():
        return 'user_channels'
    
    @staticmethod
    def get_user_detail_key(user_id):
        return f"user:detail:{user_id}"
    
    @staticmethod    
    async def get_channel_name(user_id):
        channel_name = await redis_client.hget(UserRedisService.get_channel_name_key(), user_id)
        return channel_name.decode() if channel_name else None
    
    @staticmethod
    async def cache_user_detail(user_id, user_detail: dict, ttl=21600):
        key = UserRedisService.get_user_detail_key(user_id)
        await redis_client.set(key, json.dumps(user_detail), ex=ttl)
    
    @staticmethod
    async def get_cached_user(user_id) -> dict:
        key = UserRedisService.get_user_detail_key(user_id)
        raw_data = await redis_client.get(key)
        if raw_data:
            return json.loads(raw_data)
        return None
    
    @staticmethod
    async def get_or_fetch_user(user_id, token):
        if not user_id:
            return
        cached = await UserRedisService.get_cached_user(user_id)
        if cached:
            return cached
        
        from config.services import UserService
        user_detail = await UserService.get_user(user_id, token)
        if user_detail:
            await UserRedisService.cache_user_detail(user_id, user_detail)
        
        return user_detail


class ArenaRedisService:
    @staticmethod
    def get_arena_participants_key(arena_id, user_id):
        return f'arena_participants:{arena_id, user_id}'
    
    @staticmethod
    async def set_participants(arena_id, user_id, ttl=3000):
        key = ArenaRedisService.get_arena_participants_key(arena_id, user_id)
        await redis_client.set(key, 1, ex=ttl)