from typing import List
from .models import Tournament, TournamentParticipant, TournamentMatch
import math
from config.services import UserService
from config.custom_validation_error import CustomValidationError
from config.error_type import ErrorType
from asgiref.sync import async_to_sync

class TournamentService:
    @staticmethod
    def get_websocket_url(tournament_id):
        return f"ws/tournament/{tournament_id}/"

    @staticmethod
    def join(tournament_id, user_id, token):
        tournament = Tournament.objects.get(id=tournament_id)
        
        if tournament.state != tournament.State.WAITING:
            raise CustomValidationError(ErrorType.TOURNAMENT_NOT_WAITING)
        if tournament.is_full():
            raise CustomValidationError(ErrorType.TOURNAMENT_FULL)
        if TournamentParticipant.objects.filter(tournament=tournament, user_id=user_id).exists():
            raise CustomValidationError(ErrorType.ALREADY_EXISTS)
        
        TournamentParticipant.objects.create(tournament=tournament, user_id=user_id)
        
        if tournament.is_full():
            TournamentService.start(tournament, token)

    @staticmethod
    def start(tournament:Tournament, token):
        if tournament.state != tournament.State.WAITING:
            raise CustomValidationError(ErrorType.TOURNAMENT_NOT_WAITING)
        if not tournament.is_full():
            raise CustomValidationError(ErrorType.TOURNAMENT_NOT_FULL)
        
        user_ids = TournamentService.get_participant_ids(tournament)
        
        TournamentService.set(tournament, user_ids)
        
        for user_id in user_ids:
            async_to_sync(UserService.send_notification)(user_id, {
                "type":"tournament.start",
                "tournament_id": tournament.id,
                "message": f"The tournament \"{tournament.name}\" is starting!"
            })
            
        for user_id in user_ids:
            user_email = async_to_sync(UserService.get_user_email)(user_id, token)
            subject = TournamentService.get_subject(tournament)
            message = TournamentService.get_message()
            async_to_sync(UserService.send_email)(user_email, subject, message, token)
            
    @staticmethod
    def set(tournament:Tournament, user_ids):
        matches = TournamentService.create_matches(tournament)
        TournamentService.assign_players(tournament, matches, user_ids)
        tournament.state = Tournament.State.IN_PROGRESS
        tournament.save()

    @staticmethod    
    def create_matches(tournament: Tournament) -> List[TournamentMatch]:
        matches = []
        for match_number in range(1, tournament.max_participants):
            round = tournament.total_rounds - int(math.log2(match_number))
            match = TournamentMatch.objects.create(tournament=tournament, round=round, match_number=match_number)
            matches.append(match)
            
        return matches

    @staticmethod
    def assign_players(tournament:Tournament, matches:List[TournamentMatch], user_ids):
        max_participants = tournament.max_participants
        
        for match_number in range(max_participants // 2, max_participants):
            match = matches[match_number - 1]
            i = match_number % max_participants // 2
            match.left_player = user_ids[i]
            match.right_player = user_ids[i + 1]
            match.state = match.State.READY
        
    @staticmethod
    def update_bracket(tournament_id):
        tournament = Tournament.objects.get(id=tournament_id)
        all_matches = TournamentMatch.objects.filter(tournament=tournament).all()
        pending_matches = [match for match in all_matches if match.state == TournamentMatch.State.PENDING]
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
                match.state = TournamentMatch.State.READY
                match.save()
                
    @staticmethod
    def get_subject(tournament: Tournament):
        return f"The tournament \"{tournament.name}\" has started!"
    
    @staticmethod
    def get_message():
        return "Please participate in the tournament and proceed with your matches."
    
    @staticmethod
    def get_participant_ids(tournament: Tournament):
        return TournamentParticipant.objects.filter(tournament=tournament).values_list('user_id', flat=True)