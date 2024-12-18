import asyncio
from config.custom_validation_error import CustomValidationError
from config.error_type import ErrorType
from .models import Reception
from .redis_utils import (
    is_user_in_reception,
    get_participants,
    is_invited,
    get_current_reception,
    set_redis_invitation,
    is_blacklisted,
    get_channel_name,
)
from config.services import get_user
from channels.layers import get_channel_layer
from .jwt_utils import verify_ws_token

def reception_websocket_url(reception_id):
    return f"/ws/reception/{reception_id}/"

def get_reception_group_name(reception_id):
    return f"reception_{reception_id}"

async def get_participants_count(reception_id):
    return len(await get_participants(reception_id))

async def get_participants_detail(reception_id, token):
    participants = await get_participants(reception_id)
    tasks = {k: get_user(k, token) for k in participants.keys()}
    users = await asyncio.gather(*tasks.values())
    return {user.get('nickname'): participants[k] for k, user in zip(tasks.keys(), users)}

async def validate_join_reception(reception_id, user_id, password):
    try:
        reception = await Reception.objects.aget(id=reception_id)
    except:
        raise CustomValidationError(ErrorType.RECEPTION_NOT_FOUND)
    if await get_participants_count(reception_id) >= reception.max_players:
        raise CustomValidationError(ErrorType.RECEPTION_FULL)

    invited = await is_invited(reception_id, user_id)
    
    if not invited and not reception.check_password(password):
        raise CustomValidationError(ErrorType.INVALID_PASSWORD)
    
async def invite(from_user_id, to_user_id, from_user_name):
    reception_id = await get_current_reception(from_user_id)
    if not reception_id:
        raise CustomValidationError(ErrorType.NO_RECEPTION)
    # 친구 상태 검증 해야 되나?

    channel_layer = get_channel_layer()
    channel_name = await get_channel_name(to_user_id)
    if not channel_name:
        raise CustomValidationError(ErrorType.NOT_ONLINE)
    await channel_layer.send(
        channel_name,
        {
            "type": "reception.invitation",
            "sender": from_user_name,
            "reception_id": reception_id
        }
    )
    
    await set_redis_invitation(reception_id, to_user_id)
    
async def reception_exists(reception_id):
    return await Reception.objects.filter(id=reception_id).aexists()

async def validate_user_connect(user_id, token):
    user = await get_user(user_id, token)
    if not user:
        return False
    if await is_user_in_reception(user_id):
        return False
    return True

async def validate_reception_token(user_id, reception_id, token):
    if is_blacklisted(token):
        return False
    
    payload = verify_ws_token(token)
    if not payload:
        return False
    
    if user_id != payload.get('user_id'):
        return False
    if reception_id != payload.get('reception_id'):
        return False
    return True

