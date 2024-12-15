import aiohttp
from config.settings import USER_SERVICE

async def get_user(user_id, token):
    request_url = f'{USER_SERVICE}profile/{user_id}/'
    headers = {'Authorization': f'Bearer {token}'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(request_url, headers=headers, timeout=10) as response:
            if response.status == 200:
                return await response.json()
            return None
        
async def get_user_name(user_id, token):
    user = await get_user(user_id, token)
    if not user:
        return None
    return user.get('nickname', None)
        
def get_invitation_group_name(user_id):
    return f"invitation_{user_id}"