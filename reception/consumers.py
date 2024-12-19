from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .redis_utils import (
    add_user_to_reception,
    remove_user_from_reception,
    update_user_state,
    should_remove_reception,
    should_start_arena,
    add_to_blacklist,
    set_redis_playing_reception,
    set_redis_arena_participants,
    is_playing
)
from .services import (
    get_participants_detail,
    get_reception_group_name,
    reception_exists,
    validate_user_connect,
    validate_reception_token
)
from .models import Reception
from config.close_codes import CloseCode
from urllib.parse import parse_qs
from arena.services import arena_websocket_url


class ReceptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.is_added = False
        self.reception_id = self.scope['url_route']['kwargs']['reception_id']
        self.reception_group_name = get_reception_group_name(self.reception_id)
        self.user_id = self.scope['user_id']
        
        query = parse_qs(self.scope['query_string'].decode())
        self.token = query.get('token', [None])[0]
        
        if not self.validate_access():
            await self.close(code=CloseCode.INVALID_ACCESS)
            return
        
        await self.accept()
        
        await self.channel_layer.group_add(
            self.reception_group_name,
            self.channel_name
        )
        
        await add_to_blacklist(self.token)
        await add_user_to_reception(self.reception_id, self.user_id)
        self.is_added = True
        
        await self.broadcastUserUpdate()
    
    async def validate_access(self):
        if not await validate_reception_token(self.user_id, self.reception_id, self.token):
            return False
        
        if not await reception_exists(self.reception_id):
            return False

        if not await validate_user_connect(self.user_id, self.token):
            return False
        
        return True
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.reception_group_name,
            self.channel_name
        )
            
        if self.is_added:
            await remove_user_from_reception(self.reception_id, self.user_id)
            if not await is_playing(self.reception_id) and await should_remove_reception(self.reception_id):
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
            
    async def handle_ready(self, data):
        if 'is_ready' not in data:
            await self.send(json.dumps({'error': 'is_ready field is required'}))
            return
        
        is_ready = data['is_ready']
        
        await update_user_state(self.reception_id, self.user_id, is_ready)
        
        await self.broadcastUserUpdate()
        
        if await should_start_arena(self.reception_id):
            await set_redis_playing_reception(self.reception_id)
            # 브로드캐스트
            await self.channel_layer.group_send(
                self.reception_group_name,
                {
                    'type': 'move_to_arena'
                }
            )
            
    async def move_to_arena(self, event):
        await set_redis_arena_participants(self.reception_id, self.user_id)
        await self.send(text_data=json.dumps({
            'type': 'move',
            'url': arena_websocket_url(self.reception_id)
        }))
        
        await self.channel_layer.group_discard(
            self.reception_group_name,
            self.channel_name
        )
        
    async def broadcastUserUpdate(self):
        message = await get_participants_detail(self.reception_id, self.scope['token'])
        await self.broadcast_message('participants', message)
        
    async def broadcast_message(self, message_type, message):
        await self.channel_layer.group_send(
            self.reception_group_name,
            {
                'type': 'send_to_client',
                'message_type': message_type,
                'message': message
            }
        )

    async def send_to_client(self, event):
        await self.send(text_data=json.dumps({
            'type': event['message_type'],
            'message': event['message']
        }))