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
    async def get_reception(reception_id):
        try:
            reception = await Reception.objects.aget(id=reception_id)
        except Reception.DoesNotExist:
            raise CustomValidationError(ErrorType.RECEPTION_NOT_FOUND)
        return reception
    
    @staticmethod
    async def remove(reception_id):
        await Reception.objects.filter(id=reception_id).adelete()
    
    @staticmethod
    async def set_playing(reception_id):
        reception = await ReceptionService.get_reception(reception_id)
        reception.state = Reception.State.IN_PROGRESS
        await reception.asave()

    @staticmethod
    async def is_playing(reception_id):
        reception = await ReceptionService.get_reception(reception_id)
        if reception.state == Reception.State.IN_PROGRESS:
            return True
        return False

    @staticmethod
    async def unset_playing(reception_id):
        reception = await ReceptionService.get_reception(reception_id)
        reception.state = Reception.State.WAITING
        await reception.asave()
        
    @staticmethod
    async def reset_state(reception_id):
        await ReceptionService.unset_playing(reception_id)
        await ReceptionRedisService.reset_ready_state(reception_id)
    
    @staticmethod
    async def validate_join(reception_id, user_id, password):
        try:
            reception = await Reception.objects.aget(id=reception_id)
        except Reception.DoesNotExist:
            raise CustomValidationError(ErrorType.RECEPTION_NOT_FOUND)
        current_reception_id = await ReceptionRedisService.get_current_reception(user_id)
        if current_reception_id:
            if str(current_reception_id) != str(reception_id):
                # 이전 방이 진행 중인지 확인
                try:
                    old_reception = await Reception.objects.aget(id=int(current_reception_id))
                    if old_reception.state == Reception.State.IN_PROGRESS:
                        raise CustomValidationError(ErrorType.ALREADY_ASSIGNED)
                    # 이전 방이 대기 중(게임 종료 후 잔여 Redis 데이터) → 자동 정리
                    await ReceptionRedisService.remove_user(current_reception_id, user_id)
                except Reception.DoesNotExist:
                    # 이전 방이 삭제됨 → 잔여 Redis 데이터 정리
                    await ReceptionRedisService.remove_user(current_reception_id, user_id)
                # 정리 후 인원 검사
                if await ReceptionService.get_participants_count(reception_id) >= reception.max_players:
                    raise CustomValidationError(ErrorType.RECEPTION_FULL)
            # else: 현재 들어가려는 방에 이미 참가되어있는 경우 → 통과
        else:
            # 참가한 방이 없는 경우에만 인원 검사.
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
            "content": {
                "inviter": from_user_name,
            	"reception_id": reception_id
			}
        })

        if result:
            await ReceptionRedisService.set_invitation(reception_id, to_user_id)

    @staticmethod
    async def exists(reception_id):
        return await Reception.objects.filter(id=reception_id).aexists()
