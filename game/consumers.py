from channels.generic.websocket import AsyncWebsocketConsumer
import json


class GameRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
    async def disconnect(self, close_code):
        print("disconnect")
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        print(data)