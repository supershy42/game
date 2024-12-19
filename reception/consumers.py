from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .redis_utils import (
    is_user_in_reception,
    add_user_to_reception,
    remove_user_from_reception,
    update_user_state,
    should_remove_reception,
    should_start_game,
    add_to_blacklist,
    is_blacklisted
)
from .services import get_participants_detail
from config.services import get_user
from .models import Reception
import asyncio
from config.close_codes import CloseCode
from urllib.parse import parse_qs
from .jwt_utils import verify_ws_token


class ReceptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.is_added = False
        self.reception_id = self.scope['url_route']['kwargs']['reception_id']
        self.reception_group_name = f'reception_{self.reception_id}'
        self.user_id = self.scope['user_id']
        
        query = parse_qs(self.scope['query_string'].decode())
        token = query.get('token', [None])[0]
        if not await self.validate_token(token):
            await self.close(code=CloseCode.INVALID_TOKEN)
            return
        
        if not await self.validate_reception():
            await self.close(code=CloseCode.INVALID_RECEPTION)
            return

        if not await self.validate_user():
            await self.close(code=CloseCode.INVALID_USER)
            return
        
        await self.accept()
        
        await self.channel_layer.group_add(
            self.reception_group_name,
            self.channel_name
        )
        
        await add_to_blacklist(token)
        await add_user_to_reception(self.reception_id, self.user_id)
        self.is_added = True
        
        await self.broadcastUserUpdate()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.reception_group_name,
            self.channel_name
        )
            
        if self.is_added:
            await remove_user_from_reception(self.reception_id, self.user_id)
            if await should_remove_reception(self.reception_id):
                await Reception.objects.filter(id=self.reception_id).adelete()
            else:
                await self.broadcastUserUpdate()
        
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({'error': 'json decode error'}))
            return
        message_type = data.get('type')
        
        if message_type == 'ready':
            await self.handle_ready(data)
        else:
            await self.send(json.dumps({'error': 'unknown message type'}))
            return
            
    async def validate_token(self, token):
        if is_blacklisted(token):
            return False
        
        payload = verify_ws_token(token)
        if not payload:
            return False
        
        if self.user_id != payload.get('user_id'):
            return False
        if self.reception_id != payload.get('reception_id'):
            return False
        return True
    
    async def validate_reception(self):
        return await Reception.objects.filter(id=self.reception_id).aexists()
    
    async def validate_user(self):
        user = await get_user(self.user_id, self.scope['token'])
        if not user:
            return False
        if await is_user_in_reception(self.user_id):
            return False
        return True
            
    async def handle_ready(self, data):
        if 'is_ready' not in data:
            await self.send(json.dumps({'error': 'is_ready field is required'}))
            return
        
        is_ready = data['is_ready']
        
        await update_user_state(self.reception_id, self.user_id, is_ready)
        
        await self.broadcastUserUpdate()
        
        if await should_start_game(self.reception_id):
            await self.start_game()
            
    async def start_game(self):
        await self.broadcast_message('start', {
            'message': 'Game start!'
        })
        await asyncio.sleep(3)
        await self.close(code=CloseCode.GAME_STARTED)
        
    async def broadcastUserUpdate(self):
        content = await get_participants_detail(self.reception_id, self.scope['token'])
        await self.broadcast_message('participants', content)
        
    async def broadcast_message(self, message_type, content):
        await self.channel_layer.group_send(
            self.reception_group_name,
            {
                'type': 'send_to_client',
                'message_type': message_type,
                'content': content
            }
        )

    async def send_to_client(self, event):
        await self.send(text_data=json.dumps({
            'type': event['message_type'],
            'content': event['content']
        }))