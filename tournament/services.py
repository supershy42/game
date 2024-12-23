from typing import List
from .models import Tournament, TournamentParticipant, Round, TournamentMatch
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
        
        TournamentService.set_tournament(tournament)
        round = Round.objects.get(tournament=tournament, round_number=1)
        participant_ids = TournamentService.get_participant_ids(round)
        TournamentService.notify_participants(tournament, participant_ids)
        TournamentService.send_email_to_participants(tournament, participant_ids, token)
    
    @staticmethod
    def set_tournament(tournament:Tournament):
        matches = TournamentService.create_matches(tournament)
        TournamentService.assign_players(tournament, matches)
        tournament.state = Tournament.State.IN_PROGRESS
        tournament.save()
        
    @staticmethod
    def handle_match_end(tournament_id, match_number, user_id, result):
        tournament = Tournament.objects.get(id=tournament_id)
        match = TournamentMatch.objects.get(
            round__tournament=tournament,
            match_number=match_number
        )
        if match.state == TournamentMatch.State.FINISHED:
            return
        
        if result['lp_user_id'] == user_id:
            user_score = result['lp_score']
        else:
            user_score = result['rp_score']
        if match.left_player == user_id:
            match.left_score = user_score
        else:
            match.right_score = user_score
        match.winner = result['winner']
        match.state = TournamentMatch.State.FINISHED
        match.save()

        current_round = match.round
        if current_round.round_number == tournament.total_rounds:
            # 우승
            print("final win!")
            return
        
        parent_match:TournamentMatch = match.parent_match
        if match.parent_match_player_slot == TournamentMatch.Slot.LEFT:
            parent_match.left_player = match.winner
        else:
            parent_match.right_player = match.winner
            
        if parent_match.left_player and parent_match.right_player:
            parent_match.state = TournamentMatch.State.READY
        parent_match.save()
        
        unfinished_matches = current_round.tournamentmatch_set.exclude(state=TournamentMatch.State.FINISHED)
        if unfinished_matches.exists():
            print("아직 경기 남음")
            return
        
        next_round_number = current_round.round_number + 1
        next_round = Round.objects.get(tournament=tournament, round_number=next_round_number)
        
        participant_ids = TournamentService.get_participant_ids(next_round)
        TournamentService.notify_participants(tournament, participant_ids)

    @staticmethod
    def create_matches(tournament: Tournament) -> List[TournamentMatch]:
        rounds = TournamentService.create_rounds(tournament)
        matches = []
        
        for match_number in range(1, tournament.max_participants):
            round_number = tournament.total_rounds - int(math.log2(match_number))
            round = rounds[round_number - 1]
            
            parent_match = None
            parent_match_player_slot = None
            if match_number > 1:
                parent_match = matches[(match_number // 2) - 1]
                if match_number % 2 == 0:
                    parent_match_player_slot = TournamentMatch.Slot.LEFT
                else:
                    parent_match_player_slot = TournamentMatch.Slot.RIGHT
                
            match = TournamentMatch.objects.create(
                round=round,
                match_number=match_number,
                parent_match=parent_match,
                parent_match_player_slot=parent_match_player_slot
            )
            matches.append(match)
            
        return matches
    
    @staticmethod
    def create_rounds(tournament:Tournament):
        rounds = []
        for round_number in range(1, tournament.total_rounds + 1):
            round = Round.objects.create(
                tournament=tournament,
                round_number=round_number
            )
            rounds.append(round)
        
        return rounds

    @staticmethod
    def assign_players(tournament:Tournament, matches:List[TournamentMatch]):
        max_participants = tournament.max_participants
        participant_ids = TournamentParticipant.objects.filter(tournament=tournament).values_list('user_id', flat=True)
        
        for match_number in range(max_participants // 2, max_participants):
            match = matches[match_number - 1]
            i = (match_number - max_participants // 2) * 2
            match.left_player = participant_ids[i]
            match.right_player = participant_ids[i + 1]
            match.state = match.State.READY
            match.save()
            
    @staticmethod
    def notify_participants(tournament, participant_ids):
        for user_id in participant_ids:
            async_to_sync(UserService.send_notification)(user_id, {
                "type":"tournament.start",
                "tournament_id": tournament.id,
                "message": f"The tournament \"{tournament.name}\" is starting!"
            })
            
    @staticmethod
    def send_email_to_participants(tournament, participant_ids, token):
        for user_id in participant_ids:
            user_email = async_to_sync(UserService.get_user_email)(user_id, token)
            subject = TournamentService.get_subject(tournament)
            message = TournamentService.get_message()
            async_to_sync(UserService.send_email)(user_email, subject, message, token)
                
    @staticmethod
    def get_subject(tournament: Tournament):
        return f"The tournament \"{tournament.name}\" has started!"
    
    @staticmethod
    def get_message():
        return "Please participate in the tournament and proceed with your matches."
    
    @staticmethod
    def get_participant_ids(round: Round):
        participants = []
        matches:List[TournamentMatch] = round.tournamentmatch_set.all()
        for match in matches:
            participants.append(match.left_player)
            participants.append(match.right_player)
            
        return participants