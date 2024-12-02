from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GameRoomSerializer

class CreateGameRoomView(APIView):
    def post(self, request):
        serializer = GameRoomSerializer(data=request.data)
        if serializer.is_valid():
            room = serializer.save()
            response_serializer = GameRoomSerializer(room)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )