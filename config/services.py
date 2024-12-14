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