import asyncio
from config.custom_validation_error import CustomValidationError
from config.error_type import ErrorType
from .models import Reception
from .redis_utils import get_participants, get_participants_count, is_invited, redis_invite
from config.services import get_user

def websocket_reception_url(reception_id):
    return f"/ws/reception/{reception_id}/"

async def get_participants_detail(reception_id, token):
    participants = await get_participants(reception_id)
    tasks = {k: get_user(k, token) for k in participants.keys()}
    users = await asyncio.gather(*tasks.values())
    return {user.get('nickname'): participants[k] for k, user in zip(tasks.keys(), users)}
    # result = {}
    # for k, v in participants.items():
    #     user = await get_user(k)
    #     nickname = user.get('nickname')
    #     result[nickname] = v
    # return result

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
    
# async def validate_invitation(from_user_id, to_user_id):
#     reception_id = 