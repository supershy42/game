from channels.generic.websocket import AsyncWebsocketConsumer
from .services import ArenaService
from .domain.arena import Arena
from .domain.player import Player
import json
from config.services import UserService
from .domain.arena_manager import ArenaManager
from .enums import Direction, ArenaType
from reception.services import ReceptionService
from config.redis_services import ReceptionRedisService, ArenaRedisService
from tournament.services import TournamentService
from asgiref.sync import sync_to_async
from config.close_codes import CloseCode

class ArenaConsumer(AsyncWebsocketConsumer):
    directions = {d.value for d in Direction}
    
    async def connect(self):
        await self.initialize_data()
        
        if not await self.validate_access():
            self.close(code=CloseCode.INVALID_ACCESS)
            return
        
        await self.accept()
        await self.channel_layer.group_add(self.arena_group_name, self.channel_name)
        
        self.initialize_arena()
        
    async def initialize_data(self):
        kwargs = self.scope["url_route"]["kwargs"]
        self.user_id = self.scope.get('user_id')
        self.token = self.scope.get('token')
        self.arena = None
        self.user_name = await UserService.get_user_name(self.user_id, self.token)
        
        if "arena_id" in kwargs:
            self.arena_id = self.scope['url_route']['kwargs']['arena_id']
            self.arena_group_name = ArenaService.get_group_name(self.arena_id)
            self.match = await ArenaService.get_match(self.arena_id)
            self.type = ArenaType.NORMAL
        else:
            self.tournament_id = kwargs['tournament_id']
            self.match_number = kwargs['match_number']
            self.arena_id = TournamentService.get_arena_id(self.tournament_id, self.match_number)
            self.arena_group_name = TournamentService.get_group_name(self.arena_id)
            self.type = ArenaType.TOURNAMENT
        
    async def validate_access(self):
        if self.type == ArenaType.NORMAL:
            if not await ArenaRedisService.is_allowed_user(self.arena_id, self.user_id):
                return False
            return True
        else:
            if await TournamentService.is_match_finished(self.tournament_id, self.match_number):
                return False
            if not await TournamentService.is_user_in_match(self.tournament_id, self.match_number, self.user_id):
                return False
            return True
        
    async def initialize_arena(self):
        self.arena:Arena = ArenaManager.get_arena(self.arena_id)
        self.arena.set_messenger(self.arena_group_name, self.broadcast_message)
        
        if self.type == ArenaType.TOURNAMENT:
            self.team = await TournamentService.get_user_team(self.tournament_id, self.match_number, self.user_id)
        else:
            self.team = self.arena.get_remaining_team()
        self.player = Player(self.user_id, self.arena, self.team)
        if not await self.arena.add_player(self.player):
            self.close(code=CloseCode.ARENA_FULL)
            return
        
        await self.send_json({
            'type': 'team',
            'message': self.team.value
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.arena_group_name,
            self.channel_name
        )
        
        if not self.arena:
            return
        
        if self.arena.is_started() and not self.arena.is_finished:
            self.handle_player_forfeit()
            
        await self.arena.remove_player(self.player)
        await ArenaRedisService.remove_allowed_user(self.arena_id, self.user_id)
        
    async def handle_player_forfeit(self):
        await self.broadcast_message('exit', f'{self.user_name} is exit arena.')
        await self.arena.forfeit(self.user_id)
        await ReceptionRedisService.remove_allowed_user(self.match.reception_id, self.user_id)
        await ReceptionRedisService.remove_user(self.match.reception_id, self.user_id)
        
        if await ReceptionRedisService.should_remove(self.match.reception_id):
            await ReceptionService.remove(self.match.reception_id)
        
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'move':
                await self.handle_move(data.get('direction'))
        except json.JSONDecodeError:
            await self.send_json({'error': 'json decode error'})
        
    async def handle_move(self, direction):
        if direction not in self.directions:
            await self.send_json({
                'type': 'error',
                'message': 'invalid direction' 
            })
            return
            
        self.player.move(direction)
            
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
            await sync_to_async(ArenaService.save_normal_match)(self.match, result)
            message = {
                'type': 'arena.end',
                'result': result,
                'reception_id': self.match.reception_id
            }
            await self.send_json(message)
            
            await ReceptionService.reset_state(self.match.reception_id)
        
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