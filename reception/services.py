from config.custom_validation_error import CustomValidationError
from config.error_type import ErrorType
from .models import Reception
from .redis_utils import get_participants_count, is_invited

def websocket_reception_url(reception_id):
    return f"/ws/reception/{reception_id}/"

async def validate_join_reception(reception_id, user_id, password):
    try:
        reception = await Reception.objects.aget(id=reception_id)
    except:
        raise CustomValidationError(ErrorType.RECEPTION_NOT_FOUND)
    if await get_participants_count(reception_id) >= reception.max_players:
        raise CustomValidationError(ErrorType.RECEPTION_FULL)

    invited = await is_invited(reception_id, user_id)
    print(invited)
    
    if not invited and not reception.check_password(password):
        raise CustomValidationError(ErrorType.INVALID_PASSWORD)