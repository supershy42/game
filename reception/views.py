from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ReceptionSerializer
from rest_framework.generics import ListAPIView
from .models import Reception

class CreateReceptionView(APIView):
    def post(self, request):
        serializer = ReceptionSerializer(data=request.data)
        if serializer.is_valid():
            reception = serializer.save()
            response_serializer = ReceptionSerializer(reception)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
        
class ReceptionListView(ListAPIView):
    queryset = Reception.objects.order_by('id')
    serializer_class = ReceptionSerializer
    
class ReceptionJoinView(APIView):
    def post(self, request, room_id):
        user_id = request.user_id
        user_password = request.data.get('password', None)
        
        reception = Reception.objects.get(id=room_id)
        
        invited = False # temp
        
        if invited or reception.check_password(user_password):
            ws_token = "xxx.yyy.zzz" # temp
            return Response({"status": "ok", "ws_token": ws_token}, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid password"}, status=status.HTTP_403_FORBIDDEN) 