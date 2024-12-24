from typing import List
from .models import Tournament, TournamentParticipant, Match
import math
import asyncio
from config.services import UserService
from config.custom_validation_error import CustomValidationError
from config.error_type import ErrorType
from asgiref.sync import async_to_sync

class TournamentService:
    @staticmethod
    def get_websocket_url(tournament_id):
        return f"ws/tournament/{tournament_id}/"

    @staticmethod
    def join(tournament_id, user_id):
        tournament = Tournament.objects.get(id=tournament_id)
        
        if tournament.state != tournament.State.WAITING:
            raise CustomValidationError(ErrorType.TOURNAMENT_NOT_WAITING)
        if tournament.is_full():
            raise CustomValidationError(ErrorType.TOURNAMENT_FULL)
        if TournamentParticipant.objects.filter(tournament=tournament, user_id=user_id).exists():
            raise CustomValidationError(ErrorType.ALREADY_EXISTS)
        
        TournamentParticipant.objects.create(tournament=tournament, user_id=user_id)

    @staticmethod
    def start(tournament_id, user_id):
        tournament = Tournament.objects.get(id=tournament_id)
        
        if tournament.creator != user_id:
            raise CustomValidationError(ErrorType.PERMISSION_DENIED)
        if tournament.state != tournament.State.WAITING:
            raise CustomValidationError(ErrorType.TOURNAMENT_NOT_WAITING)
        if not tournament.is_full():
            raise CustomValidationError(ErrorType.TOURNAMENT_NOT_FULL)
        
        user_ids = TournamentService.get_participant_ids(tournament)
        
        TournamentService.set(tournament, user_ids)
        
        for user_id in user_ids:
            async_to_sync(UserService.send_notification)(user_id, {
                "type":"tournament.start",
                "url": TournamentService.get_websocket_url(tournament_id),
                "message": f"The tournament \"{tournament.name}\" is starting!"
            })
            
    @staticmethod
    def set(tournament:Tournament, user_ids):
        matches = TournamentService.create_matches(tournament)
        TournamentService.assign_players(tournament, matches, user_ids)
        tournament.state = Tournament.State.IN_PROGRESS
        tournament.save()
        
    @staticmethod
    def update_bracket(tournament_id):
        tournament = Tournament.objects.get(id=tournament_id)
        all_matches = Match.objects.filter(tournament=tournament).all()
        pending_matches = [match for match in all_matches if match.state == Match.State.PENDING]
        match_dict = {match.match_number: match for match in all_matches}
        
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
                match.save()

    @staticmethod
    def assign_players(tournament:Tournament, matches:List[Match], user_ids):
        max_participants = tournament.max_participants
        
        for match_number in range(max_participants // 2, max_participants):
            match = matches[match_number - 1]
            i = match_number % max_participants // 2
            match.left_player = user_ids[i]
            match.right_player = user_ids[i + 1]
            match.state = match.State.READY

    @staticmethod    
    def create_matches(tournament: Tournament) -> List[Match]:
        matches = []
        for match_number in range(1, tournament.max_participants):
            round = tournament.total_rounds - int(math.log2(match_number))
            match = Match.objects.create(tournament=tournament, round=round, match_number=match_number)
            matches.append(match)
            
        return matches
    
    @staticmethod
    def get_participant_ids(tournament: Tournament):
        return TournamentParticipant.objects.filter(tournament=tournament).values_list('user_id', flat=True)