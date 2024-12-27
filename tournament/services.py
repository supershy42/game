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
    def get_group_name(tournament_id):
        return f"tournament_group_{tournament_id}"
    
    @staticmethod
    def get_arena_id(tournament_id, match_number):
        return f"tournament{tournament_id}_match{match_number}"
    
    @staticmethod
    async def is_user_in_match(tournament_id, match_number, user_id):
        team = await TournamentService.get_user_team(tournament_id, match_number, user_id)
        return await TournamentService.get_user_team(tournament_id, match_number, user_id) is not None
    
    @staticmethod
    async def get_user_team(tournament_id, match_number, user_id):
        match = await TournamentService.get_match(tournament_id, match_number)
        if match.left_player == user_id:
            return TournamentMatch.Team.LEFT
        elif match.right_player == user_id:
            return TournamentMatch.Team.RIGHT
    
    @staticmethod
    async def get_match(tournament_id, match_number):
        tournament = await Tournament.objects.aget(id=tournament_id)
        match = await TournamentMatch.objects.aget(
            round__tournament=tournament,
            match_number=match_number
        )
        return match
    
    @staticmethod
    async def is_match_finished(tournament_id, match_number):
        match = await TournamentService.get_match(tournament_id, match_number)
        
        if match.state == TournamentMatch.State.FINISHED:
            return True
        return False

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
        participant_ids = TournamentService.get_round_participant_ids(round)
        TournamentService.notify_round_started(tournament, participant_ids, round)
        TournamentService.send_email_to_participants(tournament, participant_ids, token)
    
    @staticmethod
    def set_tournament(tournament:Tournament):
        matches = TournamentService.create_matches(tournament)
        TournamentService.assign_players(tournament, matches)
        tournament.state = Tournament.State.IN_PROGRESS
        tournament.save()
        
    @staticmethod
    def handle_match_end(tournament_id, match_number, result):
        tournament = Tournament.objects.get(id=tournament_id)
        match = async_to_sync(TournamentService.get_match)(tournament_id, match_number)
        if match.state == TournamentMatch.State.FINISHED:
            return
        
        TournamentService.save_match_result(match, result)

        current_round = match.round
        if current_round.round_number == tournament.total_rounds:
            # 우승
            TournamentService.handle_tournament_ended(tournament, match.winner)
            return
        
        TournamentService.save_parent_match(match)
        
        unfinished_matches = current_round.tournamentmatch_set.exclude(state=TournamentMatch.State.FINISHED)
        if unfinished_matches.exists():
            # 아직 경기 남음
            return
        
        # 다음 라운드 시작
        TournamentService.handle_next_round_start(tournament, current_round)
        
    @staticmethod
    def save_match_result(match:TournamentMatch, result):
        match.left_score = result['lp_score']
        match.right_score = result['rp_score']
        match.winner = result['winner']
        match.state = TournamentMatch.State.FINISHED
        match.save()
        
    @staticmethod
    def handle_tournament_ended(tournament:Tournament, winner):
        tournament.winner = winner
        tournament.state = Tournament.State.FINISHED
        tournament.save()
        TournamentService.notify_tournament_ended(tournament)
        
    @staticmethod
    def save_parent_match(match:TournamentMatch):
        parent_match:TournamentMatch = match.parent_match
        if match.parent_match_player_team == TournamentMatch.Team.LEFT:
            parent_match.left_player = match.winner
        else:
            parent_match.right_player = match.winner
            
        if parent_match.left_player and parent_match.right_player:
            parent_match.state = TournamentMatch.State.READY
        parent_match.save()
        
    @staticmethod
    def handle_next_round_start(tournament:Tournament, current_round:Round):
        next_round_number = current_round.round_number + 1
        next_round = Round.objects.get(tournament=tournament, round_number=next_round_number)
        participant_ids = TournamentService.get_round_participant_ids(next_round)
        TournamentService.notify_round_started(tournament, participant_ids, next_round)

    @staticmethod
    def create_matches(tournament: Tournament) -> List[TournamentMatch]:
        rounds = TournamentService.create_rounds(tournament)
        matches = []
        
        for match_number in range(1, tournament.max_participants):
            round_number = tournament.total_rounds - int(math.log2(match_number))
            round = rounds[round_number - 1]
            match = TournamentService.create_match(round, match_number, matches)
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
    def create_match(round, match_number, matches):
        parent_match = None
        parent_match_player_team = None
        if match_number > 1:
            parent_match = matches[(match_number // 2) - 1]
            if match_number % 2 == 0:
                parent_match_player_team = TournamentMatch.Team.LEFT
            else:
                parent_match_player_team = TournamentMatch.Team.RIGHT
            
        match = TournamentMatch.objects.create(
            round=round,
            match_number=match_number,
            parent_match=parent_match,
            parent_match_player_team=parent_match_player_team
        )
        return match

    @staticmethod
    def assign_players(tournament:Tournament, matches:List[TournamentMatch]):
        max_participants = tournament.max_participants
        participant_ids = TournamentService.get_all_participant_ids(tournament)
        
        for match_number in range(max_participants // 2, max_participants):
            match = matches[match_number - 1]
            i = (match_number - max_participants // 2) * 2
            match.left_player = participant_ids[i]
            match.right_player = participant_ids[i + 1]
            match.state = match.State.READY
            match.save()
            
    @staticmethod
    def notify_round_started(tournament:Tournament, participant_ids, round:Round):
        for participant_id in participant_ids:
            async_to_sync(UserService.send_notification)(participant_id, {
                "type":"tournament.round.start",
                "tournament_id": tournament.id,
                "message": f"The tournament \"{tournament.name}\"'s round {round.round_number} is started!"
            })
            
    @staticmethod
    def notify_tournament_ended(tournament:Tournament):
        participant_ids = TournamentService.get_all_participant_ids(tournament)
        for participant_id in participant_ids:
            async_to_sync(UserService.send_notification)(participant_id, {
                "type":"tournament.end",
                "tournament_id": tournament.id,
                "message": f"The tournament \"{tournament.name}\" has ended! The winner is {tournament.winner}. Congratulations!"
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
    def get_round_participant_ids(round: Round):
        participants = []
        matches:List[TournamentMatch] = round.tournamentmatch_set.all()
        for match in matches:
            participants.append(match.left_player)
            participants.append(match.right_player)
            
        return participants
    
    @staticmethod
    def get_all_participant_ids(tournament:Tournament):
        return TournamentParticipant.objects.filter(tournament=tournament).values_list('user_id', flat=True)