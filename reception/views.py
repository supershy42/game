from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ReceptionSerializer, ReceptionJoinSerializer, ReceptionInvitationSerializer
from rest_framework.generics import ListAPIView
from .models import Reception
from .services import ReceptionService
from config.response_builder import response_error, response_ok
from config.custom_validation_error import CustomValidationError
from asgiref.sync import async_to_sync
from config.services import UserService
from config.redis_services import ReceptionRedisService

class CreateReceptionView(APIView):
    def post(self, request):
        serializer = ReceptionSerializer(data=request.data, context={'request': request})
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
            async_to_sync(ReceptionService.validate_join)(reception_id, user_id, password)
            async_to_sync(ReceptionRedisService.add_allowed_user)(reception_id, user_id)
            return response_ok(message={
                "url": ReceptionService.get_websocket_url(reception_id),
            })
        except CustomValidationError as e:
            return response_error(e)

class ReceptionInvitationView(APIView):
    def post(self, request):
        from_user_id = request.user_id
        serializer = ReceptionInvitationSerializer(data=request.data, context={'from_user_id': from_user_id, 'token': request.token})
        serializer.is_valid(raise_exception=True)
        to_user_id = serializer.validated_data['to_user_id']
        from_user_name = async_to_sync(UserService.get_user_name)(from_user_id, request.token)
        try:
            async_to_sync(ReceptionService.invite)(from_user_id, to_user_id, from_user_name)
            return response_ok()
        except CustomValidationError as e:
            return response_error(e)