from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .redis_utils import (
    is_user_in_reception,
    add_user_to_reception,
    remove_user_from_reception,
    update_user_state,
    should_start_game,
    get_participants
)
from config.services import get_user
from channels.db import database_sync_to_async
from .models import Reception


class ReceptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.reception_id = self.scope['url_route']['kwargs']['reception_id']
        self.reception_group_name = f'reception_{self.reception_id}'
        self.user_id = self.scope['user_id']
        self.is_added = False
        # token = self.scope['token']
        
        try:
            self.reception = await database_sync_to_async(Reception.objects.get)(id=self.reception_id)
        except Reception.DoesNotExist:
            await self.close(code=4002)  # 4002: 해당 Reception이 없음 
            return
        
        user = await get_user(self.user_id)
        if not user:
            await self.close(code=4000) # 4000: 해당 user가 없음
            return
        self.user = user
        self.user_name = self.user.get('nickname')
        
        if await is_user_in_reception(self.user_name):
            await self.close(code=4001) # 4001: 이미 소속된 방이 있음
            return
        
        await self.accept()
        
        await self.channel_layer.group_add(
            self.reception_group_name,
            self.channel_name
        )
        
        await add_user_to_reception(self.reception_id, self.user_name)
        self.is_added = True
        
        participants = await get_participants(self.reception_id)
        await self.send(text_data=json.dumps({
            'type': 'participants',
            'content': participants
        }))
        
        await self.broadcast_message('join', {
            'user_name': self.user_name
        })
        
    async def disconnect(self, close_code):
        if self.is_added:
            await remove_user_from_reception(self.reception_id, self.user_name)
            await self.broadcast_message('leave', {
                'user_name': self.user_name
            })
        
        await self.channel_layer.group_discard(
            self.reception_group_name,
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
        
        await update_user_state(self.reception_id, self.user_name, is_ready)
        
        await self.broadcast_message('ready', {
            'user_name': self.user_name,
            'is_ready': is_ready
        })
        
        if await should_start_game(self.reception_id):
            await self.start_game()
            
    async def start_game(self):
        await self.broadcast_message('start', {
            'message': 'Game start!'
        })
        await self.close(code=5000) # 5000: 게임 시작
        
    async def broadcast_message(self, message_type, content):
        await self.channel_layer.group_send(
            self.reception_group_name,
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