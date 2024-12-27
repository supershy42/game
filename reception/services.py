import asyncio
from config.custom_validation_error import CustomValidationError
from config.error_type import ErrorType
from .models import Reception
from config.redis_services import ReceptionRedisService
from config.services import UserService

class ReceptionService:
    @staticmethod
    def get_websocket_url(reception_id):
        return f"/ws/reception/{reception_id}/"

    @staticmethod
    def get_group_name(reception_id):
        return f"reception_{reception_id}"

    @staticmethod
    async def get_participants_count(reception_id):
        return len(await ReceptionRedisService.get_participants(reception_id))
    
    @staticmethod
    async def validate_join(reception_id, user_id, password):
        try:
            reception = await Reception.objects.aget(id=reception_id)
        except:
            raise CustomValidationError(ErrorType.RECEPTION_NOT_FOUND)
        current_reception_id = await ReceptionRedisService.get_current_reception(user_id)
        if current_reception_id and str(current_reception_id) != str(reception_id):
            raise CustomValidationError(ErrorType.ALREADY_ASSIGNED)
        if await ReceptionService.get_participants_count(reception_id) >= reception.max_players:
            raise CustomValidationError(ErrorType.RECEPTION_FULL)

        invited = await ReceptionRedisService.is_invited(reception_id, user_id)
        
        if not invited and not reception.check_password(password):
            raise CustomValidationError(ErrorType.INVALID_PASSWORD)
        
    @staticmethod
    async def invite(from_user_id, to_user_id, from_user_name):
        reception_id = await ReceptionRedisService.get_current_reception(from_user_id)
        if not reception_id:
            raise CustomValidationError(ErrorType.NO_RECEPTION)

        result = await UserService.send_notification(to_user_id, {
            "type": "reception.invitation",
            "sender": from_user_name,
            "reception_id": reception_id
        })

        if result:
            await ReceptionRedisService.set_invitation(reception_id, to_user_id)
        
    @staticmethod
    async def exists(reception_id):
        return await Reception.objects.filter(id=reception_id).aexists()
