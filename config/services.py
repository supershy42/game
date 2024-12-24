import aiohttp
from config.settings import USER_SERVICE_URL
from channels.layers import get_channel_layer
from .redis_utils import get_channel_name

class UserService:
    @staticmethod
    async def get_user(user_id, token):
        request_url = f'{USER_SERVICE_URL}profile/{user_id}/'
        headers = {'Authorization': f'Bearer {token}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(request_url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
            
    @staticmethod
    async def get_user_email(user_id, token):
        user = await UserService.get_user(user_id, token)
        if user:
            return user.get('email')
    
    @staticmethod
    async def send_email(email, subject, message, token):
        request_url = f'{USER_SERVICE_URL}send-email/'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = {
            'email': email,
            'subject': subject,
            'message': message
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(request_url, headers=headers, json=data, timeout=10) as response:
                if response.status == 200:
                    return True
                return False
    
    @staticmethod    
    async def get_user_name(user_id, token):
        user = await UserService.get_user(user_id, token)
        if not user:
            return None
        return user.get('nickname', None)
        
    @staticmethod    
    def get_invitation_group_name(user_id):
        return f"invitation_{user_id}"

    @staticmethod
    async def send_notification(user_id, message):
        channel_layer = get_channel_layer()
        channel_name = await get_channel_name(user_id)
        if not channel_name:
            return False
        
        await channel_layer.send(channel_name, message)
        return True