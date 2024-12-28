import redis.asyncio as redis
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
    async def add_user(reception_id, user_id):
        participants_key = ReceptionRedisService.get_participants_key(reception_id)
        await redis_client.hset(participants_key, user_id, 0)
        
        user_reception_key = ReceptionRedisService.get_user_reception_key(user_id)
        await redis_client.set(user_reception_key, reception_id)

    @staticmethod    
    async def remove_user(reception_id, user_id):    
        participants_key = ReceptionRedisService.get_participants_key(reception_id)
        await redis_client.hdel(participants_key, user_id)
        
        user_reception_key = ReceptionRedisService.get_user_reception_key(user_id)
        await redis_client.delete(user_reception_key)

    @staticmethod    
    async def update_user_state(reception_id, user_id, is_ready):
        participants_key = ReceptionRedisService.get_participants_key(reception_id)
        await redis_client.hset(participants_key, user_id, int(is_ready))

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
            return all(v == 1 for v in participants.values())
        return False

    @staticmethod
    async def get_participants(reception_id):
        participants_key = ReceptionRedisService.get_participants_key(reception_id)
        participants = await redis_client.hgetall(participants_key)
        return {k.decode(): int(v.decode()) for k, v in participants.items()}

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
    async def get_channel_name(user_id):
        channel_name = await redis_client.hget(UserRedisService.get_channel_name_key(), user_id)
        return channel_name.decode() if channel_name else None


class ArenaRedisService:
    @staticmethod
    def get_arena_participants_key(arena_id, user_id):
        return f'arena_participants:{arena_id, user_id}'
    
    @staticmethod
    async def set_participants(arena_id, user_id, ttl=3000):
        key = ArenaRedisService.get_arena_participants_key(arena_id, user_id)
        await redis_client.set(key, 1, ex=ttl)