import redis.asyncio as redis
from .services import (
    get_participants_key,
    get_user_room_key
)

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def is_user_in_room(user_name):
    user_room_key = get_user_room_key(user_name)
    existing_room = await redis_client.get(user_room_key)
    if existing_room:
        return True
    return False

async def add_user_to_room(room_id, user_name):
    participants_key = get_participants_key(room_id)
    await redis_client.hset(participants_key, user_name, 0)
    
    user_room_key = get_user_room_key(user_name)
    await redis_client.set(user_room_key, room_id)
    
async def remove_user_from_room(room_id, user_name):    
    participants_key = get_participants_key(room_id)
    await redis_client.hdel(participants_key, user_name)
    
    user_room_key = get_user_room_key(user_name)
    await redis_client.delete(user_room_key)
    
async def update_user_state(room_id, user_name, is_ready):
    participants_key = get_participants_key(room_id)
    await redis_client.hset(participants_key, user_name, int(is_ready))
    
async def should_start_game(room_id):
    participants = await get_participants(room_id)

    if len(participants) > 1:
        return all(v == 1 for v in participants.values())
    return False

async def get_participants(room_id):
    participants_key = get_participants_key(room_id)
    participants = await redis_client.hgetall(participants_key)
    return {k.decode(): int(v.decode()) for k, v in participants.items()}

