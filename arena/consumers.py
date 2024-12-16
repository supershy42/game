from channels.generic.websocket import AsyncWebsocketConsumer
from .services import get_arena_group_name

class ArenaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.arena_id = self.scope['url_route']['kwargs']['arena_id']
        self.arena_group_name = get_arena_group_name(self.arena_id)
        
        await self.accept()
        
        await self.channel_layer.group_add(
            self.reception_group_name,
            self.channel_name
        )
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.reception_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        return
        
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