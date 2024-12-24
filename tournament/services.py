from typing import List
from .models import Tournament, TournamentParticipant, Match
import math
import asyncio
from config.services import UserService
from config.custom_validation_error import CustomValidationError
from config.error_type import ErrorType

class TournamentService:
    @staticmethod
    def get_grooup_name(tournament_id):
        return f"tournament_{tournament_id}"
    
    @staticmethod
    async def get_current_participants(tournament_id: int):
        return await TournamentParticipant.objects.filter(tournament_id=tournament_id).acount()
    
    @staticmethod
    async def is_full(tournament: Tournament):
        current_count = await TournamentParticipant.objects.filter(tournament=tournament).acount()
        return current_count == tournament.max_participants

    @staticmethod
    async def join(tournament_id, user_id):
        tournament = await Tournament.objects.aget(id=tournament_id)
        
        if await TournamentParticipant.objects.filter(tournament=tournament, user_id=user_id).aexists():
            raise CustomValidationError(ErrorType.ALREADY_EXISTS)
        if await TournamentService.is_full(tournament):
            raise CustomValidationError(ErrorType.TOURNAMENT_FULL)
        if tournament.state != tournament.State.WAITING:
            raise CustomValidationError(ErrorType.TOURNAMENT_NOT_WAITING)
        
        await TournamentParticipant.objects.acreate(tournament=tournament, user_id=user_id)

    @staticmethod
    async def start(tournament_id):
        tournament = await Tournament.objects.aget(id=tournament_id)
        
        if tournament.state != tournament.State.WAITING:
            raise CustomValidationError(ErrorType.TOURNAMENT_NOT_WAITING)
        if not await TournamentService.is_full(tournament):
            raise CustomValidationError(ErrorType.TOURNAMENT_NOT_FULL)
        
        await TournamentService.set_players(tournament)
        
        user_ids = await TournamentService.get_participant_ids(tournament)
        tasks = [
            UserService.send_notification(user_id, {
                "type":"tournament.start",
                "url": TournamentService.get_grooup_name(tournament_id),
                "message": f"The tournament \"{tournament.name}\" is starting!"
            })
            for user_id in user_ids
        ]
        await asyncio.gather(*tasks)
        
    @staticmethod
    async def update_bracket(tournament_id):
        tournament = await Tournament.objects.aget(id=tournament_id)
        all_matches = await Match.objects.filter(tournament=tournament).all()
        pending_matches = [match for match in all_matches if match.state == Match.State.PENDING]
        match_dict = {match.match_number: match for match in all_matches}
        
        tasks = []
        
        for match in pending_matches:
            match_number = match.match_number
            
            if not match.left_player:
                left_child_number = match_number * 2
                if left_child_number in match_dict:
                    left_child = match_dict[left_child_number]
                    match.left_player = left_child.winner
                    
            if not match.right_player:
                right_child_number = match_number * 2 + 1
                if right_child_number in match_dict:
                    right_child = match_dict[right_child_number]
                    match.right_player = right_child.winner
                
            if match.left_player and match.right_player:
                match.state = Match.State.READY
                tasks.append(match.asave())
            
        await asyncio.gather(*tasks)

    @staticmethod
    async def set_players(tournament:Tournament):
        user_ids = await TournamentService.get_participant_ids(tournament)
        matches:List[Match] = await TournamentService.create_matches(tournament)
        max_participants = tournament.max_participants
        tasks = []
        
        async def process_match(match_number: int):
            match = matches[match_number - 1]
            i = match_number % max_participants // 2
            match.left_player = user_ids[i]
            match.right_player = user_ids[i + 1]
            match.state = match.State.READY
            await match.asave()
            
        for match_number in range(max_participants // 2, max_participants):
            tasks.append(process_match(match_number))
            
        await asyncio.gather(*tasks)

    @staticmethod    
    async def create_matches(tournament: Tournament):
        matches = []
        for match_number in range(1, tournament.max_participants):
            round = tournament.total_rounds - int(math.log2(match_number))
            match = await Match.objects.acreate(tournament=tournament, round=round, match_number=match_number)
            matches.append(match)
            
        return matches
    
    @staticmethod
    async def get_participant_ids(tournament: Tournament):
        return await TournamentParticipant.objects.filter(tournament=tournament).values_list('user_id', flat=True)