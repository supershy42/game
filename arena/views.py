from rest_framework.views import APIView
from rest_framework.response import Response
from .services import ArenaService
from .serializers import NormalMatchSerializer
from rest_framework import status
from config.services import UserService
from asgiref.sync import async_to_sync

class MatchHistoryView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not async_to_sync(UserService.get_user)(user_id, request.token):
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        matches = ArenaService.get_user_matches(user_id)
        serializer = NormalMatchSerializer(matches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)