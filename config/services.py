import aiohttp

USER_SERVICE = "http://localhost:8000/api/user/"

async def get_user(user_id):
    user_service_url = f'{USER_SERVICE}{user_id}/'
    # headers = {'Authorization': f'Bearer {token}'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(user_service_url, timeout=10) as response:
            if response.status == 200:
                return await response.json()
            return None