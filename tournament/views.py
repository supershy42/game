from rest_framework.views import APIView
from .serializers import TournamentSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from .models import Tournament
from asgiref.sync import async_to_sync
from .services import TournamentService
from config.custom_validation_error import CustomValidationError
from config.response_builder import response_error, response_ok

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
    def get(self, tournament_id):
        try:
            TournamentService.update_bracket(tournament_id)
        except CustomValidationError as e:
            return response_error(e)
        return response_ok()