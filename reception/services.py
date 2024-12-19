import asyncio
from config.custom_validation_error import CustomValidationError
from config.error_type import ErrorType
from .models import Reception
from .redis_utils import get_participants, is_invited, get_current_reception, set_redis_invitation
from config.services import get_user, get_invitation_group_name
from channels.layers import get_channel_layer

def websocket_reception_url(reception_id):
    return f"/ws/reception/{reception_id}/"

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
    await channel_layer.group_send(
        get_invitation_group_name(to_user_id), # user service에서 웹소켓 채널 관리해줘야 함
        {
            "type": "invitation_message",
            "sender": from_user_name,
            "reception_id": reception_id
        }
    )
    
    await set_redis_invitation(reception_id, to_user_id)
    
    