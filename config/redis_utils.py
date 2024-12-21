import redis.asyncio as redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_participants_key(reception_id):
    return f'reception_{reception_id}_participants'

def get_user_reception_key(user_id):
    return f'user_{user_id}_reception'

def get_invitation_key(reception_id, user_id):
    return f'invitation:{reception_id}:{user_id}'

def get_arena_participants_key(arena_id, user_id):
    return f'arena_participants:{arena_id, user_id}'

def get_playing_reception_key():
    return 'playing_reception'

def get_channel_name_key():
    return 'user_channels'

async def is_user_in_reception(user_id):
    return await get_current_reception(user_id) is not None

async def add_user_to_reception(reception_id, user_id):
    participants_key = get_participants_key(reception_id)
    await redis_client.hset(participants_key, user_id, 0)
    
    user_reception_key = get_user_reception_key(user_id)
    await redis_client.set(user_reception_key, reception_id)
    
async def remove_user_from_reception(reception_id, user_id):    
    participants_key = get_participants_key(reception_id)
    await redis_client.hdel(participants_key, user_id)
    
    user_reception_key = get_user_reception_key(user_id)
    await redis_client.delete(user_reception_key)
    
async def update_user_state(reception_id, user_id, is_ready):
    participants_key = get_participants_key(reception_id)
    await redis_client.hset(participants_key, user_id, int(is_ready))
    
async def should_remove_reception(reception_id):
    participants = await get_participants(reception_id)

    if len(participants) < 1:
        return True
    return False
    
async def should_start_arena(reception_id):
    participants = await get_participants(reception_id)

    if len(participants) > 1:
        return all(v == 1 for v in participants.values())
    return False

async def get_participants(reception_id):
    participants_key = get_participants_key(reception_id)
    participants = await redis_client.hgetall(participants_key)
    return {k.decode(): int(v.decode()) for k, v in participants.items()}

async def get_current_reception(user_id):
    user_reception_key = get_user_reception_key(user_id)
    reception_id = await redis_client.get(user_reception_key)
    if reception_id is not None:
        reception_id = reception_id.decode()
    return reception_id

async def is_invited(reception_id, user_id):
    invitation_key = get_invitation_key(reception_id, user_id)
    return await redis_client.get(invitation_key) is not None

async def set_redis_invitation(reception_id, user_id, ttl=3000): # 일단 300초
    invitation_key = get_invitation_key(reception_id, user_id)
    await redis_client.setex(invitation_key, ttl, 1)
    
async def add_to_blacklist(token, ttl=3000):
    await redis_client.sadd("blacklist", token)
    await redis_client.expire("blacklist", ttl)
    
async def is_blacklisted(token):
    return await redis_client.sismember("blacklist", token)

async def set_redis_playing_reception(reception_id):
    key = get_playing_reception_key()
    await redis_client.sadd(key, reception_id)

async def is_playing(reception_id):
    key = get_playing_reception_key()
    return await redis_client.sismember(key, reception_id)

async def remove_redis_playing_reception(reception_id):
    key = get_playing_reception_key()
    await redis_client.srem(key, reception_id)
    
async def get_channel_name(user_id):
    channel_name = await redis_client.hget(get_channel_name_key(), user_id)
    return channel_name.decode() if channel_name else None

# game

async def set_redis_arena_participants(arena_id, user_id, ttl=3000):
    key = get_arena_participants_key(arena_id, user_id)
    await redis_client.set(key, 1, ex=ttl)