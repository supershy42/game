from channels.generic.websocket import AsyncWebsocketConsumer
from .services import get_arena_group_name
from .domain.arena import Arena
from .domain.player import Player
import json
import asyncio
from config.services import get_user_name
from .domain.arena_manager import ArenaManager

class ArenaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.arena_id = self.scope['url_route']['kwargs']['arena_id']
        self.arena_group_name = get_arena_group_name(self.arena_id)
        self.user_id = self.scope.get('user_id')
        self.token = self.scope.get('token')
        self.user_name = await get_user_name(self.user_id, self.token)
        
        # redis에서 참가자 명단에 있는지 검증해야 함
        
        await self.accept()
        await self.channel_layer.group_add(self.arena_group_name, self.channel_name)
        
        self.arena:Arena = ArenaManager.get_arena(self.arena_id)
        player = Player(self.user_id, self.arena)
        team = await self.arena.add_player(player, self.broadcast_message)
        await self.send_json({
            'type': 'team',
            'message': team.value
            })
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.arena_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        return
        
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