from rest_framework.views import APIView
from .serializers import TournamentSerializer, TournamentMatchSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from .models import Tournament, TournamentMatch
from .services import TournamentService
from config.custom_validation_error import CustomValidationError
from config.response_builder import response_error, response_ok, response_errors
from .dto import TournamentMatchDTO, TournamentDTO

class TournamentCreateView(APIView):
    def post(self, request):
        serializer = TournamentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            tournament = serializer.save()
            user_id = request.user_id
            token = request.token
            data = TournamentSerializer(TournamentDTO(tournament, token).to_dict()).data
            try:
                TournamentService.join(tournament.id, user_id, token)
            except CustomValidationError as e:
                return response_error(e)
            return Response({
                "message": "Tournament created.",
                "data": data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
class TournamentListView(generics.ListAPIView):
    serializer_class = TournamentSerializer
    
    def get_queryset(self):
        tournaments = Tournament.objects.all()
        return [TournamentDTO(tournament, self.request.token).to_dict() for tournament in tournaments]
    
        
class TournamentDetailView(APIView):
    def get(self, request, tournament_id):
        matches = TournamentMatch.objects.filter(round__tournament_id=tournament_id)\
            .order_by('match_number')
            
        match_dtos = [TournamentMatchDTO(match, request.token).to_dict() for match in matches]
        serializer = TournamentMatchSerializer(match_dtos, many=True)
        tournament_bracket = serializer.data
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return response_errors("tournament does not exist.")
        tournament_dto = TournamentDTO(tournament, request.token).to_dict()
        tournament_data = TournamentSerializer(tournament_dto).data
        user_match = TournamentService.get_user_match(tournament, request.user_id)
        participants = TournamentService.get_participants_detail(tournament, request.token)
        return response_ok({
            "tournament_bracket": tournament_bracket,
            "tournament_data": tournament_data,
            "match_number": user_match,
            "participants": participants,
        })
    

class TournamentJoinView(APIView):
    def post(self, request, tournament_id):
        user_id = request.user_id
        token = request.token
        try:
            TournamentService.join(tournament_id, user_id, token)
        except CustomValidationError as e:
            return response_error(e)
        return response_ok()


class TournamentBracketView(APIView):
    def get(self, request, tournament_id):
        matches = TournamentMatch.objects.filter(round__tournament_id=tournament_id)\
            .order_by('match_number')
            
        match_dtos = [TournamentMatchDTO(match, request.token).to_dict() for match in matches]
        serializer = TournamentMatchSerializer(match_dtos, many=True)
        return Response(serializer.data)