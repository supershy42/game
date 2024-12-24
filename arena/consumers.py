from channels.generic.websocket import AsyncWebsocketConsumer
from .services import get_arena_group_name
from .domain.arena import Arena
from .domain.player import Player
import json
from config.services import UserService
from .domain.arena_manager import ArenaManager
from .enums import Direction
from reception.services import reception_websocket_url
from config.redis_utils import remove_redis_playing_reception

class ArenaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.arena_id = self.scope['url_route']['kwargs']['arena_id']
        self.arena_group_name = get_arena_group_name(self.arena_id)
        self.user_id = self.scope.get('user_id')
        self.token = self.scope.get('token')
        self.user_name = await UserService.get_user_name(self.user_id, self.token)
        
        # redis에서 참가자 명단에 있는지 검증해야 함
        
        await self.accept()
        await self.channel_layer.group_add(self.arena_group_name, self.channel_name)
        
        self.arena:Arena = ArenaManager.get_arena(self.arena_id)
        self.arena.set_messanger(self.arena_group_name, self.broadcast_message)
        self.player = Player(self.user_id, self.arena)
        self.team = await self.arena.add_player(self.player)
        await self.send_json({
            'type': 'team',
            'message': self.team.value
            })
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.arena_group_name,
            self.channel_name
        )
        
        if self.arena.is_started() and not self.arena.is_finished:
            await self.broadcast_message('exit', f'{self.user_name} is exit arena.')
            await self.arena.forfeit(self.user_id)
            
        await self.arena.remove_player(self.player)
        
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({'error': 'json decode error'})
            return
        message_type = data.get('type')
        
        if message_type == 'move':
            direction = data.get('direction')
            await self.handle_move(direction)
        
    async def handle_move(self, direction):
        if direction == Direction.UP.value:
            self.player.move(Direction.UP)
        elif direction == Direction.DOWN.value:
            self.player.move(Direction.DOWN)
        else:
            await self.send_json({
                'type': 'error',
                'message': 'invalid direction' 
                })
            
    async def arena_end(self, event):
        message = {
            'type': 'arena.end',
            'result': event['message'],
            'url': reception_websocket_url(self.arena_id)
        }
        await self.send_json(message)
        
        await remove_redis_playing_reception(self.arena_id)
        
        await self.close()
        
    async def broadcast_message(self, message_type, message):
        await self.channel_layer.group_send(
            self.arena_group_name,
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
        
    async def send_json(self, message):
        await self.send(text_data=json.dumps(message))