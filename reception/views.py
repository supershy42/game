from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ReceptionSerializer, ReceptionJoinSerializer
from rest_framework.generics import ListAPIView
from .models import Reception
from .services import websocket_reception_url, validate_join_reception
from .jwt_utils import create_ws_token
from config.response_builder import response_error, response_ok
from config.custom_validation_error import CustomValidationError
from asgiref.sync import async_to_sync

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
    def post(self, request, reception_id):
        serializer = ReceptionJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = request.user_id
        password = serializer.validated_data.get('password')
        try:
            async_to_sync(validate_join_reception)(reception_id, user_id, password)
            message = {
                "reception_ws_url": websocket_reception_url(reception_id),
                "invite_token": create_ws_token(user_id, reception_id)
            }
            return response_ok(message=message)
        except CustomValidationError as e:
            return response_error(e)

# 테스트 용 임시 invitation view
from .redis_utils import redis_invite
class ReceptionInvitationView(APIView):
    def post(self, request):
        to_user_id = request.data.get('user_id')
        reception_id = 2
        async_to_sync(redis_invite)(reception_id, to_user_id)
        return response_ok("test invite view.")