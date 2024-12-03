from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .redis_utils import (
    is_user_in_room,
    add_user_to_room,
    remove_user_from_room,
    update_user_state,
    should_start_game,
    get_participants
)
from config.services import get_user


class GameRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'gameroom_{self.room_id}'
        self.user_id = self.scope['user_id']
        self.user_name = None
        token = self.scope['token']
        user = await get_user(self.user_id, token)
        if not user:
            await self.close(code=4000) # 4000: 해당 user가 없음
            return
        self.user = user
        self.user_name = self.user.get('nickname')
        
        if await is_user_in_room(self.user_name):
            await self.close(code=4001) # 4001: 이미 소속된 방이 있음
            return
        
        await self.accept()
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await add_user_to_room(self.room_id, self.user_name)
        
        participants = await get_participants(self.room_id)
        await self.send(text_data=json.dumps({
            'type': 'participants',
            'content': participants
        }))
        
        await self.broadcast_message('join', {
            'user_name': self.user_name
        })
        
    async def disconnect(self, close_code):
        if self.room_id and self.user_name:
            await remove_user_from_room(self.room_id, self.user_name)
            await self.broadcast_message('leave', {
                'user_name': self.user_name
            })
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({'error': 'json decode error'}))
            return
        message_type = data.get('type')
        
        if message_type == 'ready':
            await self.handle_ready(data)
            
    async def handle_ready(self, data):
        if 'is_ready' not in data:
            await self.send(json.dumps({'error': 'is_ready field is required'}))
            return
        
        is_ready = data['is_ready']
        
        await update_user_state(self.room_id, self.user_name, is_ready)
        
        await self.broadcast_message('ready', {
            'user_name': self.user_name,
            'is_ready': is_ready
        })
        
        if await should_start_game(self.room_id):
            await self.start_game()
            
    async def start_game(self):
        # 로직 추가 예정
        await self.broadcast_message('start', {
            'message': 'Game start!'
        })
        
    async def broadcast_message(self, message_type, content):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_to_client',
                'message_type': message_type,
                'sender': self.channel_name,
                'content': content
            }
        )

    async def send_to_client(self, event):
        if event.get('message_type') != 'start':
            sender = event.get('sender')
            if sender == self.channel_name:
                return
        
        await self.send(text_data=json.dumps({
            'type': event['message_type'],
            'content': event['content']
        }))