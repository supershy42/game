from channels.generic.websocket import AsyncWebsocketConsumer
from .services import ArenaService
from .domain.arena import Arena
from .domain.player import Player
import json
from config.services import UserService
from .domain.arena_manager import ArenaManager
from .enums import Direction, ArenaType
from reception.services import reception_websocket_url
from config.redis_utils import remove_redis_playing_reception
from tournament.services import TournamentService
from asgiref.sync import sync_to_async
from config.close_codes import CloseCode

class ArenaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        kwargs = self.scope["url_route"]["kwargs"]
        if "arena_id" in kwargs:
            self.arena_id = self.scope['url_route']['kwargs']['arena_id']
            self.arena_group_name = ArenaService.get_arena_group_name(self.arena_id)
            self.type = ArenaType.NORMAL
        else:
            self.tournament_id = kwargs['tournament_id']
            self.match_number = kwargs['match_number']
            self.arena_id = f"tournament{self.tournament_id}_match{self.match_number}"
            self.arena_group_name = f"group_{self.arena_id}"
            self.type = ArenaType.TOURNAMENT

        self.user_id = self.scope.get('user_id')
        self.token = self.scope.get('token')
        self.arena = None        
        
        # redis에서 참가자 명단에 있는지 검증해야 함
        if not await self.validate_access():
            self.close(code=CloseCode.INVALID_ACCESS)
            return
        
        await self.accept()
        await self.channel_layer.group_add(self.arena_group_name, self.channel_name)
        
        self.user_name = await UserService.get_user_name(self.user_id, self.token)
        self.arena:Arena = ArenaManager.get_arena(self.arena_id)
        self.arena.set_messanger(self.arena_group_name, self.broadcast_message)
        if self.type == ArenaType.TOURNAMENT:
            self.team = await TournamentService.get_user_team(self.tournament_id, self.match_number, self.user_id)
        else:
            self.team = self.arena.get_remaining_team()
        self.player = Player(self.user_id, self.arena, self.team)
        result = await self.arena.add_player(self.player)
        if not result:
            self.close(code=CloseCode.ARENA_FULL)
            return
        await self.send_json({
            'type': 'team',
            'message': self.team.value
            })
        
    async def validate_access(self):
        # redis에서 참가자 명단에 있는지 검증해야 함
        if self.type == ArenaType.NORMAL:
            return True
        else:
            if await TournamentService.is_match_finished(self.tournament_id, self.match_number):
                return False
            if not await TournamentService.is_user_in_match(self.tournament_id, self.match_number, self.user_id):
                return False
            return True

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.arena_group_name,
            self.channel_name
        )
        
        if not self.arena:
            return
        
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
        result = event['message']
        if self.type == ArenaType.TOURNAMENT:
            await sync_to_async(TournamentService.handle_match_end)(self.tournament_id, self.match_number, result)
            message = {
                'type': 'tournament.arena.end',
                'result': result
            }
            await self.send_json(message)
        else:
            await sync_to_async(ArenaService.save_normal_match)(result)
            message = {
                'type': 'arena.end',
                'result': result,
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