from channels.generic.websocket import AsyncWebsocketConsumer
import json
from config.redis_services import ReceptionRedisService, ArenaRedisService
from .services import ReceptionService
from .models import Reception
from config.close_codes import CloseCode
from arena.services import ArenaService
from arena.models import NormalMatch
from asgiref.sync import sync_to_async


class ReceptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.is_added = False
        self.reception_id = self.scope['url_route']['kwargs']['reception_id']
        self.reception_group_name = ReceptionService.get_group_name(self.reception_id)
        self.user_id = self.scope['user_id']
        self.arena_id = None
        
        if not await self.validate_access():
            await self.close(code=CloseCode.INVALID_ACCESS)
            return
        
        await self.accept()
        
        await self.channel_layer.group_add(
            self.reception_group_name,
            self.channel_name
        )
        
        self.is_added = await ReceptionRedisService.add_user(self.reception_id, self.user_id, self.scope['token'])
        if not self.is_added:
            await self.loopback_user_update()
            return
        
        await self.broadcast_user_update()
    
    async def validate_access(self):
        if not await ReceptionService.exists(self.reception_id):
            return False
        if not await ReceptionRedisService.is_allowed_user(self.reception_id, self.user_id):
            return False
        return True
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.reception_group_name,
            self.channel_name
        )
            
        if self.is_added:
            if await ReceptionService.is_playing(self.reception_id):
                return
                
            await ReceptionRedisService.remove_allowed_user(self.reception_id, self.user_id)
            await ReceptionRedisService.remove_user(self.reception_id, self.user_id)
            
            if await ReceptionRedisService.should_remove(self.reception_id):
                await ReceptionService.remove(self.reception_id)
            else:
                await self.broadcast_user_update()
        
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return await self.send_error('json decode error')
        message_type = data.get('type')
        
        if message_type == 'ready':
            await self.handle_ready(data)
        else:
            return await self.send_error('unknown message type')
            
    async def handle_ready(self, data):
        await ReceptionRedisService.toggle_ready(self.reception_id, self.user_id)
        
        await self.broadcast_user_update()
        
        if await ReceptionRedisService.should_start(self.reception_id):
            arena_id = ArenaService.generate_unique_id()
            await ReceptionService.set_playing(self.reception_id)
            # 브로드캐스트
            await self.channel_layer.group_send(
                self.reception_group_name,
                {
                    'type': 'move_to_arena',
                    'arena_id': arena_id
                }
            )
            
    async def move_to_arena(self, event):
        self.arena_id = event['arena_id']
        await sync_to_async(ArenaService.create_normal_match)(self.arena_id, self.reception_id)
        
        await ArenaRedisService.add_allowed_user(self.arena_id, self.user_id)
        await self.send_json({
            'type': 'move.arena',
            'arena_id': self.arena_id
        })
        
        await self.close()
        
    async def broadcast_user_update(self):
        message = await ReceptionRedisService.get_participants(self.reception_id)
        await self.broadcast_message('participants', message)
        
    async def loopback_user_update(self):
        message = await ReceptionRedisService.get_participants(self.reception_id)
        await self.send_json({
            'type': 'participants',
            'message': message
        })
        
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
        await self.send_json({
            'type': event['message_type'],
            'message': event['message']
        })
        
    async def send_error(self, error_message):
        await self.send_json(error_message)
        
    async def send_json(self, message):
        await self.send(text_data=json.dumps(message))