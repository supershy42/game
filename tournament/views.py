from rest_framework.views import APIView
from .serializers import TournamentSerializer, TournamentMatchSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from .models import Tournament, TournamentMatch
from .services import TournamentService
from config.custom_validation_error import CustomValidationError
from config.response_builder import response_error, response_ok
from .dto import TournamentMatchDTO

class TournamentCreateView(APIView):
    def post(self, request):
        serializer = TournamentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            tournament = serializer.save()
            user_id = request.user_id
            token = request.token
            try:
                TournamentService.join(tournament.id, user_id, token)
            except CustomValidationError as e:
                return response_error(e)
            return Response({
                "message": "Tournament created.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
class TournamentListView(generics.ListAPIView):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer
        
# class TournamentDetailView(APIView):
    

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